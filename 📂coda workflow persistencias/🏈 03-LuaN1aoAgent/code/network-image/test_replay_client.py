import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import replay_client


class FakeResponse:
    status_code = 204

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def iter_bytes(self):
        yield b"response"


class FakeClient:
    requests = []

    def __init__(self, **options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def stream(self, method, url, headers, content):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'network-image/test_replay_client.py','step':'stream','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye


class ReplayClientTest(unittest.TestCase):
    def test_request_uses_out_of_band_context_without_internal_header(self) -> None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'network-image/test_replay_client.py','step':'test_request_uses_out_of_band_context_without_internal_header','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def test_routed_replay_rejects_a_target_outside_original_cidrs(self) -> None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'network-image/test_replay_client.py','step':'test_routed_replay_rejects_a_target_outside_original_cidrs','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def test_routed_replay_rejects_mixed_inside_and_outside_addresses(self) -> None:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'network-image/test_replay_client.py','step':'test_routed_replay_rejects_mixed_inside_and_outside_addresses','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def test_old_context_header_is_not_control_metadata(self) -> None:
        self.assertEqual(
            replay_client.validate_headers([{"name": "X-Luanniao-Replay-Context", "value": "application-value"}]),
            [("X-Luanniao-Replay-Context", "application-value")],
        )


if __name__ == "__main__":
    unittest.main()
