from __future__ import annotations

import json

from ai.context import AIAnalysisContext


class AIPromptBuilder:
    """
    Builds a structured prompt for an AI model.

    The AI is used as an interpretation layer.
    It does not directly execute trades.
    """

    SYSTEM_PROMPT = """
You are an advanced financial market analysis assistant.

Your job is to interpret structured market-analysis data.

You must:
1. Respect the supplied market data.
2. Never invent unavailable market information.
3. Clearly separate facts from interpretation.
4. Consider conflicting analysis methods.
5. Consider market regime and volatility.
6. Consider risk/reward information.
7. Never claim certainty.
8. Never execute trades or control a broker.
9. Explain the strongest bullish and bearish evidence.
10. Identify important contradictions and warnings.

Return a structured analytical response.
""".strip()

    def build(
        self,
        context: AIAnalysisContext,
    ) -> str:

        payload = {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "market_regime": context.market_regime,
            "market_trend": context.market_trend,
            "volatility": context.volatility,
            "confluence": {
                "direction":
                    context.confluence_direction,
                "confidence":
                    context.confluence_confidence,
                "agreement":
                    context.confluence_agreement,
                "bullish_score":
                    context.bullish_score,
                "bearish_score":
                    context.bearish_score,
                "neutral_score":
                    context.neutral_score,
            },
            "risk": {
                "risk_reward_ratio":
                    context.risk_reward_ratio,
            },
            "analyses":
                context.analyses,
            "metadata":
                context.metadata,
        }

        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

        return (
            f"{self.SYSTEM_PROMPT}\n\n"
            "MARKET ANALYSIS CONTEXT:\n"
            f"{serialized}\n\n"
            "Analyze this context and provide:\n"
            "1. Overall market bias\n"
            "2. Strongest supporting evidence\n"
            "3. Conflicting evidence\n"
            "4. Market-regime interpretation\n"
            "5. Risk considerations\n"
            "6. Key invalidation conditions\n"
            "7. Confidence level\n"
        )
