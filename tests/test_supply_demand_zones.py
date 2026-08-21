from __future__ import annotations

import pandas as pd

from analysis.supply_demand.zones import (
    SupplyDemandAnalyzer,
    SupplyDemandZone,
)


def test_supply_demand_analyzer_returns_dict():

    dataframe = pd.DataFrame(
        [
            {
                "open": 1.0,
                "high": 1.1,
                "low": 0.9,
                "close": 1.05,
            },
            {
                "open": 1.05,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
            },
            {
                "open": 1.15,
                "high": 1.3,
                "low": 1.1,
                "close": 1.25,
            },
            {
                "open": 1.25,
                "high": 1.4,
                "low": 1.2,
                "close": 1.35,
            },
            {
                "open": 1.35,
                "high": 1.5,
                "low": 1.3,
                "close": 1.45,
            },
            {
                "open": 1.45,
                "high": 1.6,
                "low": 1.4,
                "close": 1.55,
            },
        ]
    )


    analyzer = SupplyDemandAnalyzer(
        lookback=5,
    )


    result = analyzer.analyze(
        dataframe
    )


    assert isinstance(
        result,
        dict,
    )


    assert "zones" in result
    assert "bias" in result
