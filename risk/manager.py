from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Direction = Literal["long", "short"]


@dataclass(frozen=True)
class RiskParameters:
    account_balance: float
    risk_percent: float
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: Direction
    pip_size: float = 0.0001
    pip_value_per_lot: float = 10.0


@dataclass(frozen=True)
class RiskResult:
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    stop_distance_price: float
    target_distance_price: float
    stop_distance_pips: float
    target_distance_pips: float
    position_size_lots: float
    position_size_units: float
    potential_loss: float
    potential_profit: float


class RiskManager:
    """
    Risk management engine.

    Calculates:
    - Risk amount
    - Stop-loss distance
    - Take-profit distance
    - Risk/Reward ratio
    - Position size
    - Potential loss
    - Potential profit

    This class does NOT execute trades.
    """

    def __init__(
        self,
        max_risk_percent: float = 2.0,
        minimum_risk_reward: float = 1.5,
    ) -> None:

        if max_risk_percent <= 0:
            raise ValueError(
                "max_risk_percent must be greater than zero."
            )

        if minimum_risk_reward <= 0:
            raise ValueError(
                "minimum_risk_reward must be greater than zero."
            )

        self.max_risk_percent = (
            max_risk_percent
        )

        self.minimum_risk_reward = (
            minimum_risk_reward
        )

    @staticmethod
    def _validate_parameters(
        params: RiskParameters,
    ) -> None:

        if params.account_balance <= 0:
            raise ValueError(
                "account_balance must be greater than zero."
            )

        if params.risk_percent <= 0:
            raise ValueError(
                "risk_percent must be greater than zero."
            )

        if params.entry_price <= 0:
            raise ValueError(
                "entry_price must be greater than zero."
            )

        if params.stop_loss <= 0:
            raise ValueError(
                "stop_loss must be greater than zero."
            )

        if params.take_profit <= 0:
            raise ValueError(
                "take_profit must be greater than zero."
            )

        if params.pip_size <= 0:
            raise ValueError(
                "pip_size must be greater than zero."
            )

        if params.pip_value_per_lot <= 0:
            raise ValueError(
                "pip_value_per_lot must be greater than zero."
            )

        if params.direction not in (
            "long",
            "short",
        ):
            raise ValueError(
                "direction must be 'long' or 'short'."
            )

    def calculate_risk_amount(
        self,
        account_balance: float,
        risk_percent: float,
    ) -> float:

        if account_balance <= 0:
            raise ValueError(
                "account_balance must be greater than zero."
            )

        if risk_percent <= 0:
            raise ValueError(
                "risk_percent must be greater than zero."
            )

        return (
            account_balance
            * risk_percent
            / 100.0
        )

    def calculate_distances(
        self,
        params: RiskParameters,
    ) -> tuple[float, float]:

        self._validate_parameters(
            params
        )

        if params.direction == "long":

            stop_distance = (
                params.entry_price
                - params.stop_loss
            )

            target_distance = (
                params.take_profit
                - params.entry_price
            )

        else:

            stop_distance = (
                params.stop_loss
                - params.entry_price
            )

            target_distance = (
                params.entry_price
                - params.take_profit
            )

        if stop_distance <= 0:
            raise ValueError(
                "Stop-loss must be on the correct side of entry."
            )

        if target_distance <= 0:
            raise ValueError(
                "Take-profit must be on the correct side of entry."
            )

        return (
            stop_distance,
            target_distance,
        )

    def calculate_risk_reward(
        self,
        params: RiskParameters,
    ) -> float:

        (
            stop_distance,
            target_distance,
        ) = self.calculate_distances(
            params
        )

        return (
            target_distance
            / stop_distance
        )

    def calculate_position_size(
        self,
        params: RiskParameters,
    ) -> float:

        (
            stop_distance,
            _,
        ) = self.calculate_distances(
            params
        )

        stop_distance_pips = (
            stop_distance
            / params.pip_size
        )

        risk_amount = (
            self.calculate_risk_amount(
                params.account_balance,
                params.risk_percent,
            )
        )

        position_size_lots = (
            risk_amount
            / (
                stop_distance_pips
                * params.pip_value_per_lot
            )
        )

        return max(
            0.0,
            position_size_lots,
        )

    def calculate(
        self,
        params: RiskParameters,
    ) -> RiskResult:

        self._validate_parameters(
            params
        )

        if (
            params.risk_percent
            > self.max_risk_percent
        ):
            raise ValueError(
                f"Risk percent exceeds maximum "
                f"allowed risk of "
                f"{self.max_risk_percent}%."
            )

        (
            stop_distance,
            target_distance,
        ) = self.calculate_distances(
            params
        )

        risk_amount = (
            self.calculate_risk_amount(
                params.account_balance,
                params.risk_percent,
            )
        )

        risk_reward = (
            target_distance
            / stop_distance
        )

        position_size_lots = (
            self.calculate_position_size(
                params
            )
        )

        position_size_units = (
            position_size_lots
            * 100_000.0
        )

        stop_distance_pips = (
            stop_distance
            / params.pip_size
        )

        target_distance_pips = (
            target_distance
            / params.pip_size
        )

        potential_loss = (
            position_size_lots
            * stop_distance_pips
            * params.pip_value_per_lot
        )

        potential_profit = (
            position_size_lots
            * target_distance_pips
            * params.pip_value_per_lot
        )

        return RiskResult(
            risk_amount=round(
                risk_amount,
                2,
            ),
            reward_amount=round(
                risk_amount
                * risk_reward,
                2,
            ),
            risk_reward_ratio=round(
                risk_reward,
                3,
            ),
            stop_distance_price=round(
                stop_distance,
                8,
            ),
            target_distance_price=round(
                target_distance,
                8,
            ),
            stop_distance_pips=round(
                stop_distance_pips,
                2,
            ),
            target_distance_pips=round(
                target_distance_pips,
                2,
            ),
            position_size_lots=round(
                position_size_lots,
                4,
            ),
            position_size_units=round(
                position_size_units,
                2,
            ),
            potential_loss=round(
                potential_loss,
                2,
            ),
            potential_profit=round(
                potential_profit,
                2,
            ),
        )

    def is_acceptable(
        self,
        result: RiskResult,
    ) -> bool:

        return (
            result.risk_reward_ratio
            >= self.minimum_risk_reward
        )

    def summarize(
        self,
        result: RiskResult,
    ) -> dict[str, float | bool]:

        return {
            "risk_amount":
                result.risk_amount,
            "reward_amount":
                result.reward_amount,
            "risk_reward_ratio":
                result.risk_reward_ratio,
            "stop_distance_price":
                result.stop_distance_price,
            "target_distance_price":
                result.target_distance_price,
            "stop_distance_pips":
                result.stop_distance_pips,
            "target_distance_pips":
                result.target_distance_pips,
            "position_size_lots":
                result.position_size_lots,
            "position_size_units":
                result.position_size_units,
            "potential_loss":
                result.potential_loss,
            "potential_profit":
                result.potential_profit,
            "acceptable":
                self.is_acceptable(
                    result
                ),
        }
