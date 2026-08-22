
from __future__ import annotations

from dataclasses import dataclass

from config.environment import (
    get_bool_env,
    get_env,
    get_float_env,
    get_int_env,
    get_list_env,
)


@dataclass(frozen=True, slots=True)
class TelegramSettings:
    """
    Telegram bot configuration.
    """

    token: str | None = None

    enabled: bool = True

    parse_mode: str = "HTML"

    polling_timeout: int = 30

    request_timeout: float = 30.0


@dataclass(frozen=True, slots=True)
class AISettings:
    """
    AI engine configuration.

    The actual AI provider is intentionally abstracted.
    The API key and model are supplied through environment
    variables and must never be hard-coded.
    """

    api_key: str | None = None

    model: str = "gpt-5.6-luna"

    temperature: float = 0.2

    enabled: bool = False

    request_timeout: float = 60.0

    max_tokens: int = 4096


@dataclass(frozen=True, slots=True)
class OANDASettings:
    """
    OANDA market-data configuration.
    """

    api_key: str | None = None

    base_url: str = (
        "https://api-fxpractice.oanda.com/v3"
    )

    enabled: bool = True

    timeout: float = 30.0


@dataclass(frozen=True, slots=True)
class FinnhubSettings:
    """
    Finnhub market-data configuration.
    """

    api_key: str | None = None

    base_url: str = (
        "https://finnhub.io/api/v1"
    )

    enabled: bool = True

    timeout: float = 20.0


@dataclass(frozen=True, slots=True)
class AlphaVantageSettings:
    """
    Alpha Vantage market-data configuration.
    """

    api_key: str | None = None

    base_url: str = (
        "https://www.alphavantage.co/query"
    )

    enabled: bool = True

    timeout: float = 30.0


@dataclass(frozen=True, slots=True)
class MarketDataSettings:
    """
    Global market-data configuration.
    """

    default_provider: str = "oanda"

    fallback_enabled: bool = True

    fallback_providers: tuple[str, ...] = (
        "oanda",
        "finnhub",
        "alphavantage",
    )

    default_candle_limit: int = 500

    max_candle_limit: int = 5000

    cache_enabled: bool = True

    cache_ttl_seconds: int = 15


@dataclass(frozen=True, slots=True)
class AnalysisSettings:
    """
    Market-analysis configuration.

    These settings control the analysis engine rather than
    any specific trading strategy.
    """

    enabled: bool = True

    minimum_candles: int = 200

    multi_timeframe_enabled: bool = True

    confluence_enabled: bool = True

    minimum_confluence_score: float = 0.65

    minimum_signal_confidence: float = 0.70

    realtime_monitoring_enabled: bool = True

    reanalysis_enabled: bool = True

    reanalysis_interval_seconds: int = 30


@dataclass(frozen=True, slots=True)
class RiskSettings:
    """
    Risk-management configuration.

    These values are intentionally conservative defaults.
    They do not place trades by themselves.
    """

    enabled: bool = True

    risk_per_trade_percent: float = 1.0

    maximum_total_risk_percent: float = 3.0

    maximum_open_positions: int = 5

    minimum_risk_reward_ratio: float = 1.5

    maximum_risk_reward_ratio: float = 10.0

    maximum_spread_points: float = 50.0

    stop_loss_required: bool = True

    take_profit_required: bool = True


@dataclass(frozen=True, slots=True)
class MonitoringSettings:
    """
    Signal monitoring and lifecycle configuration.
    """

    enabled: bool = True

    update_interval_seconds: int = 15

    signal_expiration_minutes: int = 240

    notify_on_entry: bool = True

    notify_on_stop_loss_change: bool = True

    notify_on_take_profit_change: bool = True

    notify_on_market_reversal: bool = True

    notify_on_signal_invalidation: bool = True

    notify_on_target_hit: bool = True

    notify_on_position_close: bool = True


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """
    Application logging configuration.
    """

    level: str = "INFO"

    file_enabled: bool = True

    file_path: str = "logs/app.log"

    console_enabled: bool = True


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Global application configuration.

    All runtime configuration is loaded from environment
    variables through the load() factory.

    This object is immutable after creation.
    """

    app_name: str = "forex-signal-bot"

    environment: str = "development"

    debug: bool = False

    version: str = "1.0.0"

    telegram: TelegramSettings = TelegramSettings()

    ai: AISettings = AISettings()

    oanda: OANDASettings = OANDASettings()

    finnhub: FinnhubSettings = FinnhubSettings()

    alphavantage: AlphaVantageSettings = (
        AlphaVantageSettings()
    )

    market_data: MarketDataSettings = (
        MarketDataSettings()
    )

    analysis: AnalysisSettings = (
        AnalysisSettings()
    )

    risk: RiskSettings = RiskSettings()

    monitoring: MonitoringSettings = (
        MonitoringSettings()
    )

    logging: LoggingSettings = LoggingSettings()

    @classmethod
    def load(cls) -> "Settings":
        """
        Load complete application configuration
        from environment variables.
        """

        ai_api_key = get_env(
            "AI_API_KEY"
        )

        ai_enabled = (
            get_bool_env(
                "AI_ENABLED",
                bool(ai_api_key),
            )
        )

        fallback_providers = tuple(
            get_list_env(
                "MARKET_DATA_FALLBACK_PROVIDERS",
                [
                    "oanda",
                    "finnhub",
                    "alphavantage",
                ],
            )
        )

        return cls(
            app_name=get_env(
                "APP_NAME",
                "forex-signal-bot",
            )
            or "forex-signal-bot",

            environment=get_env(
                "APP_ENV",
                "development",
            )
            or "development",

            debug=get_bool_env(
                "DEBUG",
                False,
            ),

            version=get_env(
                "APP_VERSION",
                "1.0.0",
            )
            or "1.0.0",

            telegram=TelegramSettings(
                token=get_env(
                    "TELEGRAM_BOT_TOKEN"
                ),
                enabled=get_bool_env(
                    "TELEGRAM_ENABLED",
                    True,
                ),
                parse_mode=get_env(
                    "TELEGRAM_PARSE_MODE",
                    "HTML",
                )
                or "HTML",
                polling_timeout=get_int_env(
                    "TELEGRAM_POLLING_TIMEOUT",
                    30,
                ),
                request_timeout=get_float_env(
                    "TELEGRAM_REQUEST_TIMEOUT",
                    30.0,
                ),
            ),

            ai=AISettings(
                api_key=ai_api_key,
                model=get_env(
                    "AI_MODEL",
                    "gpt-5.6-luna",
                )
                or "gpt-5.6-luna",
                temperature=max(
                    0.0,
                    min(
                        2.0,
                        get_float_env(
                            "AI_TEMPERATURE",
                            0.2,
                        ),
                    ),
                ),
                enabled=ai_enabled,
                request_timeout=get_float_env(
                    "AI_REQUEST_TIMEOUT",
                    60.0,
                ),
                max_tokens=get_int_env(
                    "AI_MAX_TOKENS",
                    4096,
                ),
            ),

            oanda=OANDASettings(
                api_key=get_env(
                    "OANDA_API_KEY"
                ),
                base_url=get_env(
                    "OANDA_BASE_URL",
                    "https://api-fxpractice.oanda.com/v3",
                )
                or "https://api-fxpractice.oanda.com/v3",
                enabled=get_bool_env(
                    "OANDA_ENABLED",
                    True,
                ),
                timeout=get_float_env(
                    "OANDA_TIMEOUT",
                    30.0,
                ),
            ),

            finnhub=FinnhubSettings(
                api_key=get_env(
                    "FINNHUB_API_KEY"
                ),
                base_url=get_env(
                    "FINNHUB_BASE_URL",
                    "https://finnhub.io/api/v1",
                )
                or "https://finnhub.io/api/v1",
                enabled=get_bool_env(
                    "FINNHUB_ENABLED",
                    True,
                ),
                timeout=get_float_env(
                    "FINNHUB_TIMEOUT",
                    20.0,
                ),
            ),

            alphavantage=AlphaVantageSettings(
                api_key=get_env(
                    "ALPHAVANTAGE_API_KEY"
                ),
                base_url=get_env(
                    "ALPHAVANTAGE_BASE_URL",
                    "https://www.alphavantage.co/query",
                )
                or "https://www.alphavantage.co/query",
                enabled=get_bool_env(
                    "ALPHAVANTAGE_ENABLED",
                    True,
                ),
                timeout=get_float_env(
                    "ALPHAVANTAGE_TIMEOUT",
                    30.0,
                ),
            ),

            market_data=MarketDataSettings(
                default_provider=get_env(
                    "MARKET_DATA_DEFAULT_PROVIDER",
                    "oanda",
                )
                or "oanda",

                fallback_enabled=get_bool_env(
                    "MARKET_DATA_FALLBACK_ENABLED",
                    True,
                ),

                fallback_providers=fallback_providers,

                default_candle_limit=get_int_env(
                    "MARKET_DATA_DEFAULT_CANDLE_LIMIT",
                    500,
                ),

                max_candle_limit=get_int_env(
                    "MARKET_DATA_MAX_CANDLE_LIMIT",
                    5000,
                ),

                cache_enabled=get_bool_env(
                    "MARKET_DATA_CACHE_ENABLED",
                    True,
                ),

                cache_ttl_seconds=get_int_env(
                    "MARKET_DATA_CACHE_TTL_SECONDS",
                    15,
                ),
            ),

            analysis=AnalysisSettings(
                enabled=get_bool_env(
                    "ANALYSIS_ENABLED",
                    True,
                ),

                minimum_candles=get_int_env(
                    "ANALYSIS_MINIMUM_CANDLES",
                    200,
                ),

                multi_timeframe_enabled=get_bool_env(
                    "ANALYSIS_MULTI_TIMEFRAME_ENABLED",
                    True,
                ),

                confluence_enabled=get_bool_env(
                    "ANALYSIS_CONFLUENCE_ENABLED",
                    True,
                ),

                minimum_confluence_score=get_float_env(
                    "ANALYSIS_MINIMUM_CONFLUENCE_SCORE",
                    0.65,
                ),

                minimum_signal_confidence=get_float_env(
                    "ANALYSIS_MINIMUM_SIGNAL_CONFIDENCE",
                    0.70,
                ),

                realtime_monitoring_enabled=get_bool_env(
                    "ANALYSIS_REALTIME_MONITORING_ENABLED",
                    True,
                ),

                reanalysis_enabled=get_bool_env(
                    "ANALYSIS_REANALYSIS_ENABLED",
                    True,
                ),

                reanalysis_interval_seconds=get_int_env(
                    "ANALYSIS_REANALYSIS_INTERVAL_SECONDS",
                    30,
                ),
            ),

            risk=RiskSettings(
                enabled=get_bool_env(
                    "RISK_ENABLED",
                    True,
                ),

                risk_per_trade_percent=get_float_env(
                    "RISK_PER_TRADE_PERCENT",
                    1.0,
                ),

                maximum_total_risk_percent=get_float_env(
                    "RISK_MAX_TOTAL_PERCENT",
                    3.0,
                ),

                maximum_open_positions=get_int_env(
                    "RISK_MAX_OPEN_POSITIONS",
                    5,
                ),

                minimum_risk_reward_ratio=get_float_env(
                    "RISK_MIN_RR",
                    1.5,
                ),

                maximum_risk_reward_ratio=get_float_env(
                    "RISK_MAX_RR",
                    10.0,
                ),

                maximum_spread_points=get_float_env(
                    "RISK_MAX_SPREAD_POINTS",
                    50.0,
                ),

                stop_loss_required=get_bool_env(
                    "RISK_STOP_LOSS_REQUIRED",
                    True,
                ),

                take_profit_required=get_bool_env(
                    "RISK_TAKE_PROFIT_REQUIRED",
                    True,
                ),
            ),

            monitoring=MonitoringSettings(
                enabled=get_bool_env(
                    "MONITORING_ENABLED",
                    True,
                ),

                update_interval_seconds=get_int_env(
                    "MONITORING_UPDATE_INTERVAL_SECONDS",
                    15,
                ),

                signal_expiration_minutes=get_int_env(
                    "MONITORING_SIGNAL_EXPIRATION_MINUTES",
                    240,
                ),

                notify_on_entry=get_bool_env(
                    "MONITORING_NOTIFY_ON_ENTRY",
                    True,
                ),

                notify_on_stop_loss_change=get_bool_env(
                    "MONITORING_NOTIFY_ON_SL_CHANGE",
                    True,
                ),

                notify_on_take_profit_change=get_bool_env(
                    "MONITORING_NOTIFY_ON_TP_CHANGE",
                    True,
                ),

                notify_on_market_reversal=get_bool_env(
                    "MONITORING_NOTIFY_ON_REVERSAL",
                    True,
                ),

                notify_on_signal_invalidation=get_bool_env(
                    "MONITORING_NOTIFY_ON_INVALIDATION",
                    True,
                ),

                notify_on_target_hit=get_bool_env(
                    "MONITORING_NOTIFY_ON_TARGET_HIT",
                    True,
                ),

                notify_on_position_close=get_bool_env(
                    "MONITORING_NOTIFY_ON_CLOSE",
                    True,
                ),
            ),

            logging=LoggingSettings(
                level=(
                    get_env(
                        "LOG_LEVEL",
                        "INFO",
                    )
                    or "INFO"
                ).upper(),

                file_enabled=get_bool_env(
                    "LOG_FILE_ENABLED",
                    True,
                ),

                file_path=get_env(
                    "LOG_FILE_PATH",
                    "logs/app.log",
                )
                or "logs/app.log",

                console_enabled=get_bool_env(
                    "LOG_CONSOLE_ENABLED",
                    True,
                ),
            ),
        )

    def validate(self) -> None:
        """
        Validate configuration consistency.

        This method should be called during application startup.
        """

        valid_environments = {
            "development",
            "testing",
            "staging",
            "production",
        }

        if self.environment not in valid_environments:
            raise ValueError(
                f"Unsupported APP_ENV: {self.environment}"
            )

        if self.market_data.default_candle_limit < 1:
            raise ValueError(
                "Default candle limit must be greater than zero."
            )

        if (
            self.market_data.max_candle_limit
            < self.market_data.default_candle_limit
        ):
            raise ValueError(
                "Maximum candle limit cannot be lower "
                "than default candle limit."
            )

        if not 0.0 <= self.analysis.minimum_confluence_score <= 1.0:
            raise ValueError(
                "Minimum confluence score must be between 0 and 1."
            )

        if not 0.0 <= self.analysis.minimum_signal_confidence <= 1.0:
            raise ValueError(
                "Minimum signal confidence must be between 0 and 1."
            )

        if self.risk.risk_per_trade_percent <= 0:
            raise ValueError(
                "Risk per trade must be greater than zero."
            )

        if self.risk.maximum_total_risk_percent <= 0:
            raise ValueError(
                "Maximum total risk must be greater than zero."
            )

        if (
            self.risk.minimum_risk_reward_ratio <= 0
        ):
            raise ValueError(
                "Minimum risk/reward ratio must be greater than zero."
            )

        if (
            self.risk.maximum_risk_reward_ratio
            < self.risk.minimum_risk_reward_ratio
        ):
            raise ValueError(
                "Maximum risk/reward ratio cannot be lower "
                "than minimum risk/reward ratio."
            )

        if self.risk.maximum_open_positions < 1:
            raise ValueError(
                "Maximum open positions must be at least one."
            )

        if self.monitoring.update_interval_seconds < 1:
            raise ValueError(
                "Monitoring update interval must be at least one second."
            )


settings = Settings.load()

