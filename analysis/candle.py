"""Compatibility import for the canonical market candle model.

The project previously contained a second, analysis-only Candle dataclass.
That created two incompatible candle types across the data and analysis
layers.  The canonical model now lives in :mod:`data.models`.

Keep this module as a compatibility import so existing analysis imports do
not break while ensuring every layer uses the same Candle class.
"""

from data.models import Candle

__all__ = ["Candle"]
