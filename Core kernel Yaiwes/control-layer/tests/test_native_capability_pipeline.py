import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from capabilities.timesfm_native import TimesFMAdapter
from native_capability_pipeline import run_native_capability_pipeline


class NativeCapabilityPipelineTests(unittest.TestCase):
    def test_kernel_detects_implicit_temporal_intent(self):
        series = [float(i) for i in range(40)]
        out = run_native_capability_pipeline(
            op_type="READ",
            payload={"series": series, "horizon": 3},
            goal="pronóstico de demanda para los próximos 3 períodos",
            execute_capability=False,
        )
        self.assertEqual(out["native_capability"]["selected"], "temporal.forecast")

    def test_missing_runtime_is_fail_closed(self):
        series = [float(i) for i in range(40)]
        out = run_native_capability_pipeline(
            op_type="READ",
            payload={"series": series, "horizon": 3},
            goal="forecast próximos períodos",
            execute_capability=True,
            timesfm_adapter=TimesFMAdapter(),
        )
        self.assertEqual(out["capability_result"]["status"], "capability_unavailable")


if __name__ == "__main__":
    unittest.main()
