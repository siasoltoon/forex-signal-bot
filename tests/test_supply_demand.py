from __future__ import annotations

import pytest

from analysis.supply_demand import (
    SupplyDemandDetector,
    SupplyDemandResult,
    PriceZone,
)



def test_supply_demand_returns_result() -> None:

    detector = SupplyDemandDetector()


    candles = [
        {
            "open": 1.0,
            "high": 1.2,
            "low": 0.9,
            "close": 1.1,
        },
        {
            "open": 1.1,
            "high": 1.5,
            "low": 1.0,
            "close": 1.4,
        },
        {
            "open": 1.4,
            "high": 1.45,
            "low": 1.2,
            "close": 1.25,
        },
    ]


    result = detector.analyze(
        candles
    )


    assert isinstance(
        result,
        SupplyDemandResult,
    )



def test_detect_supply_zone() -> None:

    detector = SupplyDemandDetector()


    candles = [
        {
            "open": 1.0,
            "high": 1.2,
            "low": 0.9,
            "close": 1.1,
        },
        {
            "open": 1.1,
            "high": 1.6,
            "low": 1.0,
            "close": 1.5,
        },
        {
            "open": 1.5,
            "high": 1.55,
            "low": 1.3,
            "close": 1.35,
        },
    ]


    result = detector.analyze(
        candles
    )


    assert len(
        result.supply_zones
    ) >= 1


    assert isinstance(
        result.supply_zones[0],
        PriceZone,
    )



def test_detect_demand_zone() -> None:

    detector = SupplyDemandDetector()


    candles = [
        {
            "open": 1.5,
            "high": 1.6,
            "low": 1.2,
            "close": 1.3,
        },
        {
            "open": 1.3,
            "high": 1.4,
            "low": 1.0,
            "close": 1.1,
        },
        {
            "open": 1.1,
            "high": 1.3,
            "low": 0.9,
            "close": 1.25,
        },
    ]


    result = detector.analyze(
        candles
    )


    assert len(
        result.demand_zones
    ) >= 1



def test_invalid_candles() -> None:

    detector = SupplyDemandDetector()


    with pytest.raises(
        ValueError
    ):
        detector.analyze(
            [
                {
                    "open": 1.0,
                }
            ]
        )
