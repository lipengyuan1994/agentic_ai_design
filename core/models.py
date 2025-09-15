from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class IndicatorResult(BaseModel):
    indicator: str = Field(..., description="Indicator name, e.g., RSI, MACD")
    signal: str = Field(..., description="Primary signal, e.g., Oversold, Bullish Crossover")
    details: Optional[str] = Field(None, description="Human-readable details about the signal")
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional extra numeric/text metrics for the indicator"
    )


class SummaryResult(BaseModel):
    summary_text: str = Field(..., description="Human-readable summary of the analysis")
    method: Literal["openai", "local_fallback"] = Field(
        ..., description="How the summary was generated"
    )
    model: Optional[str] = Field(None, description="Model used, when applicable")


class OrchestratorPlan(BaseModel):
    ticker: str
    period: str = "1y"
    requested_indicators: Optional[List[str]] = None
    plan_indicators: List[str] = Field(
        default_factory=list, description="Ordered list of indicator names to execute"
    )
    class IndicatorPlanItem(BaseModel):
        name: str = Field(..., description="Indicator name, e.g., RSI, MACD")
        params: Dict[str, Any] = Field(
            default_factory=dict, description="Per-indicator parameters (e.g., window sizes)"
        )

    plan_items: List[IndicatorPlanItem] = Field(
        default_factory=list,
        description="Ordered items with per-indicator parameters",
    )
    rationale: Optional[str] = Field(None, description="Why these indicators and ordering")
    strategy: Optional[str] = Field(None, description="High-level plan/approach")
    max_workers: Optional[int] = Field(None, description="Suggested parallelism cap")


class AnalysisReport(BaseModel):
    ticker: str
    period: str = "1y"
    generated_at: datetime
    indicators: List[IndicatorResult]
    summary: SummaryResult
    plan: Optional[OrchestratorPlan] = None
