"""FastAPI router for analysis endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException

from advisor.analyzers.portfolio_analyzer import get_portfolio_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/analyze/portfolio/{portfolio_id}")
async def analyze_portfolio(
    portfolio_id: UUID,
    background_tasks: BackgroundTasks,
):
    """Trigger portfolio analysis (runs in background).

    Args:
        portfolio_id: Portfolio UUID
        background_tasks: FastAPI background tasks

    Returns:
        Job status with job_id
    """
    job_id = f"portfolio-{portfolio_id}-{int(__import__('time').time())}"

    # Add analysis task to background
    background_tasks.add_task(_run_portfolio_analysis, portfolio_id, job_id)

    return {
        "job_id": job_id,
        "portfolio_id": str(portfolio_id),
        "status": "queued",
        "message": "포트폴리오 분석이 시작되었습니다. 30-60초 소요됩니다.",
    }


async def _run_portfolio_analysis(portfolio_id: UUID, job_id: str):
    """Run portfolio analysis (background task).

    Args:
        portfolio_id: Portfolio UUID
        job_id: Job identifier for tracking
    """
    try:
        logger.info(f"[{job_id}] Starting portfolio analysis")

        analyzer = get_portfolio_analyzer()
        result = await analyzer.analyze(portfolio_id)

        logger.info(f"[{job_id}] Portfolio analysis completed successfully")
        logger.info(
            f"[{job_id}] Scores - Health: {result.health_score}, "
            f"Risk: {result.risk_score}, "
            f"Diversification: {result.diversification_score}"
        )

    except Exception as e:
        logger.error(f"[{job_id}] Portfolio analysis failed: {e}", exc_info=True)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-advisor",
        "version": "0.1.0",
    }
