"""Portfolio analysis using Gemini LLM."""

import json
import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI

from advisor.config import settings
from advisor.data.aggregator import (
    fetch_portfolio_analysis_data,
    save_portfolio_insight,
)
from advisor.data.models import PortfolioAnalysisContext, PortfolioAnalysisResult
from advisor.prompts.portfolio_ko import format_portfolio_prompt

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """Analyzer for portfolio health and rebalancing suggestions."""

    def __init__(self):
        """Initialize portfolio analyzer with Gemini."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
        )

    async def analyze(self, portfolio_id: UUID) -> PortfolioAnalysisResult:
        """Analyze portfolio and generate insights.

        Args:
            portfolio_id: Portfolio UUID

        Returns:
            PortfolioAnalysisResult with analysis
        """
        logger.info(f"Starting portfolio analysis for {portfolio_id}")

        # 1. Fetch data
        context = await fetch_portfolio_analysis_data(portfolio_id)

        # 2. Format prompt
        prompt = format_portfolio_prompt(context)
        logger.debug(f"Prompt generated: {len(prompt)} characters")

        # 3. Call Gemini
        try:
            response = await self.llm.ainvoke(prompt)
            response_text = response.content

            # Parse JSON response
            # Gemini might wrap JSON in markdown code blocks, so clean it
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result_data = json.loads(response_text)

            # 4. Create result object with structured data
            result = PortfolioAnalysisResult(
                portfolio_id=portfolio_id,
                analysis_date=date.today(),
                title=result_data["title"],
                executive_summary=result_data["executive_summary"],
                full_report=result_data["full_report"],
                health_score=Decimal(str(result_data["health_score"])),
                risk_score=Decimal(str(result_data["risk_score"])),
                diversification_score=Decimal(str(result_data["diversification_score"])),
                performance_score=Decimal(str(result_data.get("performance_score", 0.5))),
                key_findings=result_data["key_findings"],
                rebalancing_considerations=result_data["rebalancing_considerations"],
                insights_data=result_data["insights_data"],
                recommendations_data=result_data["recommendations_data"],
                sectors_data=result_data["sectors_data"],
                risk_metrics=result_data["risk_metrics"],
                generated_by=settings.gemini_model,
            )

            # 5. Save to database
            await save_portfolio_insight(result, context.user_id)

            logger.info(f"Portfolio analysis completed for {portfolio_id}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}", exc_info=True)
            raise


# Singleton instance
_portfolio_analyzer: PortfolioAnalyzer | None = None


def get_portfolio_analyzer() -> PortfolioAnalyzer:
    """Get or create portfolio analyzer instance."""
    global _portfolio_analyzer
    if _portfolio_analyzer is None:
        _portfolio_analyzer = PortfolioAnalyzer()
    return _portfolio_analyzer
