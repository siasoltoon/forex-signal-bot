"""Cross-cutting runtime contracts for the Trading Intelligence Platform."""

from .data_runtime import Candle, DataQuality, DataValidator, Market, MarketRequest, MarketSnapshot, ProviderManager
from .provider_runtime import AsyncRateLimiter, ProviderHealthRegistry, ProviderAttempt, ResilientProviderManager, RetryPolicy
from .analysis_runtime import AnalysisEvidence, AnalysisOrchestrator, AnalyzerRegistry, MultiTimeframeEvidence
from .analysis_plugins import AnalysisContext, AnalyzerPlugin, PluginAnalyzerRegistry, PluginOrchestrator
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
from .real_providers import AlphaVantageProvider, OandaProvider, TwelveDataProvider, configured_providers
from .research_engine import BacktestResult, ExecutionSimulator, Fill, Order, Strategy, monte_carlo as executable_monte_carlo, run_backtest, walk_forward as executable_walk_forward
from .live_runtime import AlertEngine, LiveEvent as RuntimeLiveEvent, LiveMonitor as RuntimeLiveMonitor, LiveSignal as RuntimeLiveSignal, TradeLifecycle, TradeState as RuntimeTradeState
from .persistence_security import SQLiteStore, SecretManager, StoredAnalysis
from .ml_runtime import Evaluation, ModelOutput as MLModelOutput, ProbabilisticModel, ChampionChallenger as MLChampionChallenger
from .news_macro_runtime import EventRisk, EventRiskEngine as RuntimeEventRiskEngine, MacroEvent as RuntimeMacroEvent, MacroProvider as RuntimeMacroProvider, NewsEvent as RuntimeNewsEvent, NewsProvider as RuntimeNewsProvider
from .real_analyzers import MomentumAnalyzer, TrendAnalyzer, VolatilityAnalyzer, default_real_analyzers
from .strategy_runtime import MovingAverageCrossStrategy, StrategyDNA
from .production_pipeline import ProductionAnalysisPipeline
from .pc_worker import PCWorker, from_environment as worker_from_environment

from .pipeline import IntelligencePipeline, PipelineRequest, PipelineResult
from .platform_orchestrator import PlatformOrchestrator, RuntimeHealth
__all__ = [
    "Candle", "DataQuality", "DataValidator", "Market", "MarketRequest", "MarketSnapshot", "ProviderManager",
    "AnalysisEvidence", "AnalysisOrchestrator", "AnalyzerRegistry", "MultiTimeframeEvidence", "AdvancedFusion", "IntelligenceDecision", "Scenario",
    "PortfolioRisk", "PortfolioRiskEngine", "PositionPlan", "RiskEngine", "RiskLimits", "Backtester", "ExecutionCosts", "HistoricalReplay", "walk_forward",
    "ResearchIntegrity", "MonteCarloResult", "detect_integrity", "monte_carlo", "LiveEvent", "LiveMonitor", "LiveSignal", "TradeState", "Job", "JobQueue", "JobStatus", "WorkerHeartbeat", "WorkerRegistry",
    "EventRiskEngine", "MacroEvent", "ModelOutput", "ModelRegistry", "NewsImpactAggregator", "AuditEvent", "AuditLog", "ChampionChallenger", "HealthRegistry", "HealthStatus",
    "DecisionTrace", "FinalRuntime", "RuntimeRequest", "RuntimeResult", "ModelGateway", "ModelInput", "ContractModelOutput", "ModelProvider", "MacroEventContract", "NewsEvent", "NewsProvider", "MacroProvider",
    "WorkerInfo", "WorkerJob", "RuntimeWorkerRegistry", "WorkerState", "ReportPreferences", "TelegramReportBuilder", "AlphaVantageProvider", "OandaProvider", "TwelveDataProvider", "configured_providers",
    "BacktestResult", "ExecutionSimulator", "Fill", "Order", "Strategy", "run_backtest", "executable_walk_forward", "executable_monte_carlo", "AlertEngine", "RuntimeLiveEvent", "RuntimeLiveMonitor", "RuntimeLiveSignal", "TradeLifecycle", "RuntimeTradeState",
    "SQLiteStore", "SecretManager", "StoredAnalysis", "Evaluation", "MLModelOutput", "ProbabilisticModel", "MLChampionChallenger", "EventRisk", "RuntimeEventRiskEngine", "RuntimeMacroEvent", "RuntimeMacroProvider", "RuntimeNewsEvent", "RuntimeNewsProvider",
    "MomentumAnalyzer", "TrendAnalyzer", "VolatilityAnalyzer", "default_real_analyzers", "MovingAverageCrossStrategy", "StrategyDNA", "PipelineRequest", "ProductionAnalysisPipeline", "PCWorker", "worker_from_environment", "IntelligencePipeline",
"PipelineResult","PlatformOrchestrator","RuntimeHealth",

]
