"""Tests for KIS authentication clients."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

from quote_pipeline.ingestors.kis_pure.kis_auth import (
    KisRestAuthClient,
    KisWsAuthClient,
    TokenResponse,
    ApprovalResponse,
)
from quote_pipeline.ingestors.kis_pure.kis_config import KisConfig


@pytest.fixture
def kis_config():
    """Create a test KisConfig."""
    return KisConfig(
        app_key="test_app_key",
        app_secret="test_app_secret",
        is_vts=True,
    )


@pytest.fixture
def mock_session():
    """Create a mock requests.Session."""
    return Mock()


class TestKisWsAuthClient:
    """Tests for KisWsAuthClient."""

    def test_init_with_no_cache(self, kis_config):
        """Test initialization without cached approval key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "test_ws_token.json"
            client = KisWsAuthClient(kis_config, token_path=token_path)
            
            assert client.cfg == kis_config
            assert client.session is not None
            assert client._approval is None
            assert client.approval_key is None
            assert client.token_path == token_path

    def test_init_with_cached_approval_key(self, kis_config):
        """Test initialization with cached approval key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "test_ws_token.json"
            
            # Create a cached approval key file
            cached_data = {
                "access": {
                    "access_token": "cached_approval_key_123",
                    "token_type": "Bearer",
                    "expires_in": 0,
                    "access_token_token_expired": "",
                },
                "expires_at": None,
            }
            token_path.write_text(json.dumps(cached_data))
            
            client = KisWsAuthClient(kis_config, token_path=token_path)
            
            assert client._approval is not None
            assert client.approval_key == "cached_approval_key_123"

    def test_approval_key_property(self, kis_config):
        """Test approval_key property."""
        client = KisWsAuthClient(kis_config)
        
        # Initially None
        assert client.approval_key is None
        
        # Set approval
        client._approval = ApprovalResponse(approval_key="test_key")
        assert client.approval_key == "test_key"

    def test_issue_approval_key(self, kis_config, mock_session):
        """Test issuing approval key and saving to cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "test_ws_token.json"
            
            # Mock response
            mock_response = Mock()
            mock_response.json.return_value = {"approval_key": "new_approval_key_456"}
            mock_session.post.return_value = mock_response
            
            client = KisWsAuthClient(kis_config, session=mock_session, token_path=token_path)
            approval = client.issue_approval_key()
            
            # Verify API call
            assert mock_session.post.called
            call_args = mock_session.post.call_args
            assert "/oauth2/Approval" in call_args[0][0]
            
            # Verify response
            assert approval.approval_key == "new_approval_key_456"
            assert client._approval.approval_key == "new_approval_key_456"
            assert client.approval_key == "new_approval_key_456"
            
            # Verify cache file was created
            assert token_path.exists()
            cached_data = json.loads(token_path.read_text())
            assert cached_data["access"]["access_token"] == "new_approval_key_456"


class TestKisRestAuthClient:
    """Basic tests for KisRestAuthClient."""

    def test_init_with_no_cache(self, kis_config):
        """Test initialization without cached token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "test_rest_token.json"
            client = KisRestAuthClient(kis_config, token_path=token_path)
            
            assert client.cfg == kis_config
            assert client.session is not None
            assert client._access is None
            assert client.access_token is None
            assert client.token_path == token_path
