"""Korean prompts for portfolio analysis."""

PORTFOLIO_HEALTH_CHECK_PROMPT = """당신은 월스트리트 출신의 수석 포트폴리오 전략가(Chief Portfolio Strategist)입니다.
당신의 임무는 이 포트폴리오에 대해 기관 투자자 리포트 수준의 깊이 있는 분석과 전략을 제공하는 것입니다.
냉철하고 전문적인 어조를 사용하되, 개인 투자자가 이해할 수 있도록 명확하게 설명하세요.

**중요**: 이 분석은 정보 제공 목적이며, 투자 권유나 매매 추천이 아닙니다.

## 포트폴리오 정보
- 포트폴리오명: {portfolio_name}
- 총 평가액: ₩{total_value:,.0f}
- 보유 종목 수: {position_count}개
- 기준 통화: {base_currency}

## 보유 종목
{positions_summary}

## 최근 성과 (30일)
{metrics_summary}

## 최근 관련 뉴스 (7일)
{news_summary}

---

다음 항목을 분석하여 JSON 형식으로 응답하세요:

1. **포트폴리오 건강도** (health_score: 0-1)
   - 종목 구성의 적절성
   - 섹터/지역 분산 정도
   - 전반적인 포트폴리오 품질

2. **리스크 평가** (risk_score: 0-1, 높을수록 위험)
   - 특정 종목/섹터 집중도
   - 변동성 수준 (추정치)
   - 잠재적 위험 요인

3. **다각화 점수** (diversification_score: 0-1)
   - 자산 분산 정도
   - 상관관계가 낮은 자산 보유 여부

4. **성과 점수** (performance_score: 0-1, 선택사항)
   - 최근 수익률 추세
   - 벤치마크 대비 성과 (있는 경우)

5. **구조화된 인사이트** (insights_data)
   - 3-5개의 핵심 인사이트 (전문가적 관점)
   - 각 인사이트는 type(warning/positive/neutral), title, description, impact(high/medium/low) 포함

6. **AI 추천사항** (recommendations_data)
   - 2-4개의 실행 가능한 전략적 제안
   - 각 추천은 action(rebalance/add/reduce/hold), title, description, priority(high/medium/low) 포함

7. **섹터 분포** (sectors_data)
   - 주요 섹터별 비중 (%)
   - 각 섹터에 name, percentage, color 포함
   - color는 hex 코드

8. **상세 리스크 지표** (risk_metrics)
   - level: 리스크 수준 ("안정", "보통", "다소 높음", "매우 높음")
   - volatility: 연환산 변동성 (%) - *데이터 부족시 추정치 사용, 불가능하면 0*
   - sharpe_ratio: 샤프 비율 - *산출 불가시 0 또는 null*
   - beta: 베타 계수 (시장 민감도)
   - max_drawdown: 최대 낙폭 (%)

9. **분석 리포트 텍스트**
   - title: 리포트 제목 (예: "성장 잠재력은 높으나 변동성 관리가 필요한 포트폴리오")
   - executive_summary: 핵심 요약 (Investment Highlight). 3-4문장으로 투자자가 가장 먼저 알아야 할 핵심 메시지를 강력하게 전달하세요.
   - full_report: 상세 분석 리포트 (Markdown 포맷).
     - 제목(#)과 소제목(##)을 적절히 사용하여 구조화하세요.
     - 다음 섹션을 포함하세요: [시장 현황 및 포트폴리오 포지셔닝], [주요 종목 심층 분석], [리스크 요인 점검], [향후 대응 전략].
     - 수치와 데이터를 기반으로 구체적인 근거를 제시하세요.

JSON 응답 형식:
{
  "health_score": 0.75,
  "risk_score": 0.45,
  "diversification_score": 0.60,
  "performance_score": 0.70,
  "title": "2026년 하반기 포트폴리오 전략: 변동성 관리와 성장 확보",
  "executive_summary": "현재 포트폴리오는 기술주 중심의 고성장 전략을 취하고 있으나, 최근 금리 인상 기조 하에서 변동성 위험이 확대되고 있습니다. 특히 반도체 섹터 비중(45%) 과다는 단기 성과에 부담으로 작용할 수 있습니다. 현금 비중 확대를 통해 낙폭 과대 시 줍줍 기회를 노리는 'Barbell 전략'을 제안합니다.",
  "full_report": "# 포트폴리오 정밀 진단 리포트\n\n## 1. 시장 현황 및 포트폴리오 포지셔닝\n현재 글로벌 증시는 인플레이션 둔화와 경기 침체 우려가 공존하는 국면입니다...\n\n## 2. 주요 종목 심층 분석\n**삼성전자**와 **NVIDIA**가 차지하는 비중이 과도하여...",
  "key_findings": [
    "주요 발견사항 1",
    "주요 발견사항 2",
    "주요 발견사항 3"
  ],
  "rebalancing_considerations": [
    "참고사항 1 (정보 제공)",
    "참고사항 2 (정보 제공)"
  ],
  "insights_data": [
    {
      "type": "warning",
      "title": "섹터 집중도 높음",
      "description": "기술주 비중이 68%로 높아요. 섹터 분산을 고려해보세요.",
      "impact": "high"
    },
    {
      "type": "positive",
      "title": "수익률 양호",
      "description": "최근 3개월 수익률이 시장 평균 대비 우수해요.",
      "impact": "medium"
    }
  ],
  "recommendations_data": [
    {
      "action": "rebalance",
      "title": "리밸런싱 제안",
      "description": "기술주 비중을 50%로 줄이고, 채권 ETF 추가를 권장해요.",
      "priority": "high"
    },
    {
      "action": "add",
      "title": "분산 투자",
      "description": "방어주(유틸리티, 필수소비재) 편입으로 안정성을 높여보세요.",
      "priority": "medium"
    }
  ],
  "sectors_data": [
    {
      "name": "기술",
      "percentage": 68.0,
      "color": "#3B82F6"
    },
    {
      "name": "금융",
      "percentage": 15.0,
      "color": "#10B981"
    },
    {
      "name": "헬스케어",
      "percentage": 10.0,
      "color": "#8B5CF6"
    },
    {
      "name": "기타",
      "percentage": 7.0,
      "color": "#94A3B8"
    }
  ],
  "risk_metrics": {
    "level": "다소 높음",
    "volatility": 24.5,
    "sharpe_ratio": 1.42,
    "beta": 1.15,
    "max_drawdown": -12.3
  }
}

**주의**: 반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
"""


def format_portfolio_prompt(context: "PortfolioAnalysisContext") -> str:
    """Format portfolio analysis prompt with context data.

    Args:
        context: PortfolioAnalysisContext

    Returns:
        Formatted prompt string
    """
    # Format positions summary
    positions_lines = []
    for p in context.positions[:10]:  # Top 10 positions
        value = float(p.average_cost * p.quantity)
        positions_lines.append(
            f"- {p.name} ({p.symbol}): {p.quantity} 주, "
            f"평단가 {p.currency} {p.average_cost:,.0f}, "
            f"평가액 약 {p.currency} {value:,.0f}"
        )

    positions_summary = "\n".join(positions_lines)
    if len(context.positions) > 10:
        positions_summary += f"\n... 외 {len(context.positions) - 10}개 종목"

    # Format metrics summary
    if context.metrics:
        latest = context.metrics[0]
        metrics_summary = f"""
- 총 평가액: ₩{latest.total_value:,.0f}
- 총 투자원금: ₩{latest.total_cost:,.0f}
- 수익: ₩{latest.total_pnl:,.0f} ({latest.total_pnl_percent:.2f}%)
- 변동성: {latest.volatility or 'N/A'}
- 샤프 비율: {latest.sharpe_ratio or 'N/A'}
- 최대 낙폭: {latest.max_drawdown or 'N/A'}%
""".strip()
    else:
        metrics_summary = "최근 성과 데이터 없음"

    # Format news summary
    if context.related_news:
        news_lines = []
        for news in context.related_news[:5]:
            sentiment = "긍정" if (news.sentiment_score or 0) > 0.6 else "부정" if (news.sentiment_score or 0) < 0.4 else "중립"
            news_lines.append(
                f"- [{news.source}] {news.title} ({news.published_at.strftime('%m/%d')}, {sentiment})"
            )
        news_summary = "\n".join(news_lines)
    else:
        news_summary = "최근 관련 뉴스 없음"

    return PORTFOLIO_HEALTH_CHECK_PROMPT.format(
        portfolio_name=context.portfolio_name,
        total_value=float(context.total_value_krw),
        position_count=context.position_count,
        base_currency=context.base_currency,
        positions_summary=positions_summary,
        metrics_summary=metrics_summary,
        news_summary=news_summary,
    )
