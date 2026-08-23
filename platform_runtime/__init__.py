"""Cross-cutting runtime contracts for the Trading Intelligence Platform."""

from .data_runtime import Candle, DataQuality, DataValidator, Market, MarketRequest, MarketSnapshot, ProviderManager
from .analysis_runtime import AnalysisEvidence, AnalysisOrchestrator, AnalyzerRegistry, MultiTimeframeEvidence
from .intelligence import AdvancedFusion, IntelligenceDecision, Scenario
from .risk_portfolio import PortfolioRisk, PortfolioRiskEngine, PositionPlan, RiskEngine, RiskLimits
from .research import Backtester, ExecutionCosts, HistoricalReplay, walk_forward
from .research_quality import ResearchIntegrity, MonteCarloResult, detect_integrity, monte_carlo
from .live import LiveEvent, LiveMonitor, LiveSignal, TradeState
from .worker import Job, JobQueue, JobStatus, WorkerHeartbeat, WorkerRegistry
from .ai_macro import EventRiskEngine, MacroEvent, ModelOutput, ModelRegistry, NewsImpactAggregator
from .production import AuditEvent, AuditLog, ChampionChallenger, HealthRegistry, HealthStatus
from .final_runtime import DecisionTrace, FinalRuntime, RuntimeRequest, RuntimeResult
from .ai_contracts import ModelGateway, ModelInput, ModelOutput as ContractModelOutput, ModelProvider
from .news_macro import MacroEvent as MacroEventContract, NewsEvent, NewsProvider, MacroProvider
from .worker_runtime import WorkerInfo, WorkerJob, WorkerRegistry as RuntimeWorkerRegistry, WorkerState
from .telegram_reporting import ReportPreferences, TelegramReportBuilder

__all__ = [
    "Candle", "DataQuality", "DataValidator", "Market", "MarketRequest", "MarketSnapshot", "ProviderManager",
    "AnalysisEvidence", "AnalysisOrchestrator", "AnalyzerRegistry", "MultiTimeframeEvidence",
    "AdvancedFusion", "IntelligenceDecision", "Scenario",
    "PortfolioRisk", "PortfolioRiskEngine", "PositionPlan", "RiskEngine", "RiskLimits",
    "Backtester", "ExecutionCosts", "HistoricalReplay", "walk_forward",
    "ResearchIntegrity", "MonteCarloResult", "detect_integrity", "monte_carlo",
    "LiveEvent", "LiveMonitor", "LiveSignal", "TradeState",
    "Job", "JobQueue", "JobStatus", "WorkerHeartbeat", "WorkerRegistry",
    "EventRiskEngine", "MacroEvent", "ModelOutput", "ModelRegistry", "NewsImpactAggregator",
    "AuditEvent", "AuditLog", "ChampionChallenger", "HealthRegistry", "HealthStatus",
    "DecisionTrace", "FinalRuntime", "RuntimeRequest", "RuntimeResult",
    "ModelGateway", "ModelInput", "ContractModelOutput", "ModelProvider",
    "MacroEventContract", "NewsEvent", "NewsProvider", "MacroProvider",
    "WorkerInfo", "WorkerJob", "RuntimeWorkerRegistry", "WorkerState",
    "ReportPreferences", "TelegramReportBuilder",
]
