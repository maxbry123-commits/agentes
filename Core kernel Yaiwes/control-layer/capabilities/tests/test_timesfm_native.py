import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capabilities.timesfm_native import (
    TimesFMAdapter,
    anomaly_from_intervals,
    execute_native_capability,
    route_native_capability,
)


class TimesFMNativeCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.series = [float(i) for i in range(40)]

    def test_explicit_forecast_routes(self):
        d = route_native_capability("", {
            "task": {"requires_temporal_forecast": True},
            "series": self.series,
            "horizon": 5,
        })
        self.assertEqual(d.selected, "temporal.forecast")

    def test_implicit_forecast_routes_without_model_name(self):
        d = route_native_capability(
            "Pronóstico de demanda futura para los próximos 5 períodos",
            {"series": self.series, "horizon": 5},
        )
        self.assertEqual(d.selected, "temporal.forecast")

    def test_non_temporal_task_does_not_route(self):
        d = route_native_capability(
            "Clasifica estas etiquetas",
            {"series": self.series, "horizon": 5},
        )
        self.assertIsNone(d.selected)

    def test_runtime_missing_fails_closed(self):
        out = execute_native_capability(
            "forecast próximos períodos",
            {"series": self.series, "horizon": 3},
            adapter=TimesFMAdapter(endpoint=None, mcp_endpoint=None, local_command=None),
        )
        self.assertEqual(out["status"], "capability_unavailable")
        self.assertNotIn("result", out)

    def test_structured_forecast_contract(self):
        fake = TimesFMAdapter(
            transport=lambda req: {
                "point_forecast": [[41.0, 42.0]],
                "quantiles": {"q10": [[40.0, 41.0]], "q90": [[42.0, 43.0]]},
                "metadata": {"model": "google/timesfm-test-runtime"},
            }
        )
        out = execute_native_capability(
            "proyectar tendencia",
            {"series": self.series, "horizon": 2, "return_quantiles": True},
            adapter=fake,
        )
        self.assertEqual(out["status"], "ok")
        result = out["result"]
        self.assertEqual(result["provider"], "timesfm")
        self.assertIn("point_forecast", result)
        self.assertIn("quantiles", result)
        self.assertIn("metadata", result)

    def test_anomaly_is_derived_capability(self):
        out = anomaly_from_intervals([1.0, 9.0], [0.0, 0.0], [2.0, 3.0])
        self.assertTrue(out["derived_capability"])
        self.assertEqual(out["anomaly_count"], 1)


if __name__ == "__main__":
    unittest.main()
