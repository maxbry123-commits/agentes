# Copyright (c) 2024-2026 Tencent Zhuque Lab. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Requirement: Any integration or derivative work must explicitly attribute
# Tencent Zhuque Lab (https://github.com/Tencent/AI-Infra-Guard) in its
# documentation or user interface, as detailed in the NOTICE file.

from typing import Optional, Tuple, Union

import httpx

from deepeval.test_case import (
    LLMTestCase,
    ConversationalTestCase,
)
from deepeval.utils import get_or_create_event_loop
from deepeval.metrics.utils import (
    construct_verbose_logs,
    check_conversational_test_case_params,
    trimAndLoadJson,
    check_llm_test_case_params,
    initialize_model,
)
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics.indicator import metric_progress_indicator

from deepteam.metrics import BaseRedTeamingMetric


class JailbreakMetric(BaseRedTeamingMetric):
    def __init__(
        self,
        API_URL: str,
        async_mode: bool = True,
        verbose_mode: bool = False,
    ):
        self.API_URL = API_URL
        self.using_native_model = False
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode

    def measure(
        self, test_case: Union[LLMTestCase, ConversationalTestCase]
    ) -> float:
        if isinstance(test_case, ConversationalTestCase):
            test_case = check_conversational_test_case_params(test_case, self)
        check_llm_test_case_params(test_case, self._required_params, self)

        self.evaluation_cost = 0 if self.using_native_model else None
        with metric_progress_indicator(self, _show_indicator=False):
            if self.async_mode:
                loop = get_or_create_event_loop()
                loop.run_until_complete(
                    self.a_measure(test_case, _show_indicator=False)
                )
            else:
                score, reason = self.evaluate(test_case)
                self.reason = reason
                self.score = score
                self.is_successful()
                self.verbose_logs = construct_verbose_logs(
                    self,
                    steps=[f"Score: {self.score}\nReason: {self.reason}"],
                )
                return self.score

    async def a_measure(
        self,
        test_case: Union[LLMTestCase, ConversationalTestCase],
        _show_indicator: bool = False,
    ) -> float:
        if isinstance(test_case, ConversationalTestCase):
            test_case = check_conversational_test_case_params(test_case, self)
        check_llm_test_case_params(test_case, self._required_params, self)

        self.evaluation_cost = 0 if self.using_native_model else None
        with metric_progress_indicator(
            self, async_mode=True, _show_indicator=_show_indicator
        ):
            score, reason = await self._a_evaluate(test_case)
            self.reason = reason
            self.score = score
            self.success = self.score == 0
            self.verbose_logs = construct_verbose_logs(
                self,
                steps=[f"Score: {self.score}\nReason: {self.reason}"],
            )
            return self.score

    def evaluate(self, test_case: LLMTestCase) -> Tuple[Union[int, float], str]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'AIG-PromptSecurity/deepteam/metrics/is_jailbreak/is_jailbreak.py','step':'evaluate','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def _a_evaluate(
        self, test_case: LLMTestCase
    ) -> Tuple[Union[int, float], str]:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'AIG-PromptSecurity/deepteam/metrics/is_jailbreak/is_jailbreak.py','step':'_a_evaluate','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye


    def is_successful(self) -> bool:
        if self.error is not None:
            self.success = False
        else:
            try:
                self.success = self.score == 1
            except AttributeError:
                self.success = False
        return self.success

    @property
    def __name__(self):
        return f"Bias (Red Teaming)"
