from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CalibrationResult:
    calibrated: float
    reliability_error: float

class ConfidenceCalibrator:
    def calibrate(self, raw: float, historical_accuracy: float, disagreement: float, data_quality: float) -> CalibrationResult:
        raw = max(0.0, min(1.0, raw))
        accuracy = max(0.0, min(1.0, historical_accuracy))
        disagreement = max(0.0, min(1.0, disagreement))
        quality = max(0.0, min(1.0, data_quality))
        calibrated = raw * (0.5 + 0.5 * accuracy) * (1.0 - 0.6 * disagreement) * quality
        reliability_error = abs(calibrated - accuracy)
        return CalibrationResult(max(0.0, min(1.0, calibrated)), reliability_error)
