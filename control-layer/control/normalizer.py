# -*- coding: utf-8 -*-
"""control/normalizer.py — Input Normalizer 0% LLM.
Fuente: SALIDA 4 pipeline (conceptual 1º; impl A5 por deps).
Texto/dict → forma canónica para fingerprint.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Union


_WS = re.compile(r"\s+")


def normalize(input_data: Union[str, Dict[str, Any], None]) -> str:
    """Canónico: lower, espacios colapsados, dict→json sorted."""
    if input_data is None:
        return ""
    if isinstance(input_data, dict):
        text = json.dumps(input_data, sort_keys=True, default=str)
    else:
        text = str(input_data)
    text = text.strip().lower()
    return _WS.sub(" ", text)
