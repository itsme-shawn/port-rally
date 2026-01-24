"""
KIS 순수 REST/WebSocket 인증 헬퍼.
- REST: 접근토큰(/oauth2/tokenP) 발급 + 파일 캐시
- WS: 승인키(/oauth2/Approval) 발급
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

from quote_pipeline.clients.kis import KisConfig

logger = logging.getLogger(__name__)


def _get_token_cache_path(default_filename: str) -> Path:
    """
    환경변수에서 토큰 캐시 경로를 가져옵니다.

    Args:
        default_filename: 환경변수가 없을 때 사용할 기본 파일명

    Returns:
        토큰 캐시 파일 경로
    """
    try:
        cache_dir_env = os.getenv("KIS_TOKEN_CACHE_DIR")
        if cache_dir_env:
            cache_path = Path(cache_dir_env) / default_filename
            logger.info("Using token cache path from KIS_TOKEN_CACHE_PATH: %s", cache_path)
            return cache_path
        else:
            default_path = Path(__file__).resolve().parent / default_filename
            logger.info("KIS_TOKEN_CACHE_DIR not set, using default path: %s", default_path)
            return default_path
    except Exception as err:
        default_path = Path(__file__).resolve().parent / default_filename
        logger.warning(
            "Failed to read KIS_TOKEN_CACHE_PATH from environment: %s. Using default: %s",
            err,
            default_path,
        )
        return default_path


@dataclass
class TokenRequestBody:
    grant_type: str
    appkey: str
    appsecret: str


@dataclass
class TokenResponse:
    access_token: str
    token_type: str
    expires_in: float
    access_token_token_expired: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "TokenResponse":
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=float(data.get("expires_in", 0)),
            access_token_token_expired=data.get("access_token_token_expired", ""),
        )


@dataclass
class ApprovalResponse:
    approval_key: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ApprovalResponse":
        return cls(approval_key=data["approval_key"])


@dataclass
class ApprovalRequestBody:
    grant_type: str
    appkey: str
    secretkey: str


def load_token_from_file(token_path: Path) -> tuple[Optional[TokenResponse], Optional[datetime]]:
    """
    REST 토큰 캐시 로더 (TokenResponse 전용).
    """
    try:
        if not token_path.exists():
            return None, None
        data = json.loads(token_path.read_text())
        access_raw = data.get("access")
        access = TokenResponse.from_json(access_raw) if access_raw else None
        exp_raw = data.get("expires_at")
        expires_at = datetime.fromisoformat(exp_raw) if exp_raw else None
        logger.info("Loaded cached token from %s (expires_at=%s)", token_path, expires_at)
        return access, expires_at
    except Exception as err:
        logger.warning("Failed to load token cache from %s: %s", token_path, err)
        return None, None


def save_token_to_file(token_path: Path, access: Optional[TokenResponse], expires_at: Optional[datetime]) -> None:
    """
    REST 토큰 캐시 저장 (TokenResponse 전용).
    """
    try:
        payload = {
            "access": access.__dict__ if access else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(json.dumps(payload))
        logger.info("Saved token cache to %s", token_path)
    except Exception as err:
        logger.warning("Failed to save token cache to %s: %s", token_path, err)


def read_json_cache(token_path: Path) -> Optional[Dict[str, Any]]:
    """
    단순 JSON 캐시 로더 (WS 승인키 등 공용).
    """
    try:
        if not token_path.exists():
            return None
        return json.loads(token_path.read_text())
    except Exception as err:
        logger.warning("Failed to read cache %s: %s", token_path, err)
        return None


def write_json_cache(token_path: Path, payload: Dict[str, Any]) -> None:
    """
    단순 JSON 캐시 저장 (WS 승인키 등 공용).
    """
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(json.dumps(payload))
        logger.info("Saved cache to %s", token_path)
    except Exception as err:
        logger.warning("Failed to save cache %s: %s", token_path, err)


class KisRestAuthClient:
    """
    접근토큰(/oauth2/tokenP) 발급 및 캐시 관리.
    """

    def __init__(self, config: KisConfig, session: Optional[requests.Session] = None, token_path: Optional[Path] = None) -> None:
        load_dotenv()
        self.cfg = config
        self.session = session or requests.Session()
        self._access: Optional[TokenResponse] = None
        self._expires_at: Optional[datetime] = None
        self.token_path = token_path or _get_token_cache_path("token_cache_rest.json")
        self._access, self._expires_at = load_token_from_file(self.token_path)

    @property
    def access_token(self) -> Optional[str]:
        return self._access.access_token if self._access else None

    def _parse_expiry(self, resp: TokenResponse) -> datetime:
        # 우선 access_token_token_expired(YYYY-MM-DD HH:MM:SS) 파싱 시도, 실패 시 expires_in 초 기준
        if resp.access_token_token_expired:
            try:
                return datetime.strptime(resp.access_token_token_expired, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                logger.warning("Failed to parse access_token_token_expired: %s", resp.access_token_token_expired)
        return datetime.now(timezone.utc) + timedelta(seconds=resp.expires_in)

    def get_valid_access_token(self, buffer_sec: int = 60) -> str:
        """
        캐시된 토큰이 유효하면 재발급하지 않고 그대로 반환.
        만료가 임박(버퍼 내)이면 새 토큰 발급.
        """
        if self._access and self._expires_at:
            if datetime.now(timezone.utc) + timedelta(seconds=buffer_sec) < self._expires_at:
                logger.info(
                    "Reusing cached access_token (expires_at=%s, now=%s)",
                    self._expires_at,
                    datetime.now(timezone.utc),
                )
                return self._access.access_token
        logger.info("Cached token missing or expiring soon. Requesting new token.")
        resp = self.issue_access_token()
        return resp.access_token

    def issue_access_token(self) -> TokenResponse:
        """
        POST /oauth2/tokenP
        Body: grant_type=client_credentials, appkey, appsecret
        """
        url = f"{self.cfg.base_url}/oauth2/tokenP"
        body = TokenRequestBody(
            grant_type="client_credentials",
            appkey=self.cfg.app_key,
            appsecret=self.cfg.app_secret,
        )
        logger.info("Requesting access_token: %s", url)
        resp = self.session.post(url, json=body.__dict__, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("access_token response: %s", data)
        self._access = TokenResponse.from_json(data)
        self._expires_at = self._parse_expiry(self._access)
        save_token_to_file(self.token_path, self._access, self._expires_at)
        logger.info(
            "access_token issued (expires_in=%s, expires_at=%s)",
            self._access.expires_in,
            self._expires_at,
        )
        return self._access


class KisWsAuthClient:
    """WebSocket Approval Key 발급/캐시 클라이언트."""

    def __init__(
        self,
        config: KisConfig,
        session: Optional[requests.Session] = None,
        token_path: Optional[Path] = None,
        validity_seconds: int = 24 * 3600, # approval key : 24시간
        # ref. (https://apiportal.koreainvestment.com/apiservice-apiservice?/oauth2/Approval)
    ) -> None:
        load_dotenv()
        self.cfg = config
        self.session = session or requests.Session()
        self.token_path = token_path or _get_token_cache_path("token_cache_ws.json")
        self.validity_seconds = validity_seconds
        self._approval: Optional[ApprovalResponse] = None
        self._expires_at: Optional[datetime] = None
        self._load_cache()

    def get_valid_approval_key(self, buffer_sec: int = 60) -> str:
        if self._approval and self._expires_at:
            now = datetime.now(timezone.utc)
            if now + timedelta(seconds=buffer_sec) < self._expires_at:
                logger.info(
                    "Reusing cached approval_key (expires_at=%s, now=%s)",
                    self._expires_at,
                    now,
                )
                return self._approval.approval_key
        logger.info("Cached approval_key missing or expiring. Requesting new one.")
        return self.issue_approval_key().approval_key

    def issue_approval_key(self, max_retries: int = 3) -> ApprovalResponse:
        """
        POST /oauth2/Approval
        Body: grant_type=client_credentials, appkey, secretkey
        Header: content-type

        Args:
            max_retries: 최대 재시도 횟수 (기본: 3)
        """
        url = f"{self.cfg.base_url}/oauth2/Approval"
        headers = {"content-type": "application/json; charset=utf-8"}
        body = ApprovalRequestBody(
            grant_type="client_credentials",
            appkey=self.cfg.app_key,
            secretkey=self.cfg.app_secret,
        )

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Requesting approval_key (attempt %d/%d): %s", attempt, max_retries, url)
                resp = self.session.post(url, headers=headers, json=body.__dict__, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                logger.debug("approval_key response: %s", data)
                approval = ApprovalResponse.from_json(data)
                self._approval = approval
                self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.validity_seconds)
                self._save_cache()
                logger.info("approval_key issued (expires_at=%s)", self._expires_at)
                return approval
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = attempt * 2  # 2초, 4초, 6초...
                    logger.warning(
                        "approval_key request failed (attempt %d/%d): %s. Retrying in %d seconds...",
                        attempt,
                        max_retries,
                        e,
                        wait_time,
                    )
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error("approval_key request failed after %d attempts: %s", max_retries, e)
                    raise
            except Exception as e:
                logger.error("Unexpected error while requesting approval_key: %s", e)
                raise

        # 모든 재시도 실패
        raise last_error if last_error else RuntimeError("Failed to issue approval_key")

    def _load_cache(self) -> None:
        data = read_json_cache(self.token_path)
        if not data:
            return
        try:
            key = data.get("approval_key")
            exp_raw = data.get("expires_at")
            if key:
                self._approval = ApprovalResponse(approval_key=key)
            if exp_raw:
                self._expires_at = datetime.fromisoformat(exp_raw)
            logger.info("Loaded cached approval_key from %s (expires_at=%s)", self.token_path, self._expires_at)
        except Exception as err:
            logger.warning("Failed to parse approval cache from %s: %s", self.token_path, err)
            self._approval = None
            self._expires_at = None

    def _save_cache(self) -> None:
        payload = {
            "approval_key": self._approval.approval_key if self._approval else None,
            "expires_at": self._expires_at.isoformat() if self._expires_at else None,
        }
        write_json_cache(self.token_path, payload)
