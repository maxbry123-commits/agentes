from .utils import BashTool
    
bash_tool = BashTool(root_dir="/Users/user/Desktop/ExperimentAgents/tmp")
print(bash_tool.forward("python abc.py"))

class VLLMModel(Model):
    """Model to use [vLLM](https://docs.vllm.ai/) for fast LLM inference and serving.

    Parameters:
        model_id (`str`):
            The Hugging Face model ID to be used for inference.
            This can be a path or model identifier from the Hugging Face model hub.
        model_kwargs (`dict[str, Any]`, *optional*):
            Additional keyword arguments to pass to the vLLM model (like revision, max_model_len, etc.).
    """

    def __init__(
        self,
        model_id,
        model_kwargs: dict[str, Any] | None = None,
        sampling_params_kwargs: dict[str, Any] | None = None,
        **kwargs,
    ):
        if not is_package_available("vllm"):
            raise ModuleNotFoundError("Please install 'vllm' extra to use VLLMModel: `pip install 'smolagents[vllm]'`")

        from vllm import LLM  # type: ignore
        from vllm import SamplingParams  # type: ignore
        from vllm.transformers_utils.tokenizer import get_tokenizer  # type: ignore

        self.model_kwargs = model_kwargs or {}
        super().__init__(**kwargs)
        self.model_id = model_id
        self.model = LLM(model=model_id, **self.model_kwargs)
        assert self.model is not None
        if sampling_params_kwargs is not None:
            self.sampling_params = SamplingParams(**sampling_params_kwargs)
        else:
            self.sampling_params = None
        self.tokenizer = get_tokenizer(model_id)
        self._is_vlm = False  # VLLMModel does not support vision models yet.

    def cleanup(self):
        import gc

        import torch
        from vllm.distributed.parallel_state import (  # type: ignore
            destroy_distributed_environment,
            destroy_model_parallel,
        )

        destroy_model_parallel()
        if self.model is not None:
            # taken from https://github.com/vllm-project/vllm/issues/1908#issuecomment-2076870351
            del self.model.llm_engine.model_executor.driver_worker
        gc.collect()
        destroy_distributed_environment()
        torch.cuda.empty_cache()

    def generate(
        self,
        messages: list[ChatMessage | dict],
        stop_sequences: list[str] | None = None,
        response_format: dict[str, str] | None = None,
        tools_to_call_from: list[Tool] | None = None,
        **kwargs,
    ) -> ChatMessage:
        from vllm import SamplingParams  # type: ignore

        completion_kwargs = self._prepare_completion_kwargs(
            messages=messages,
            flatten_messages_as_text=(not self._is_vlm),
            stop_sequences=stop_sequences,
            tools_to_call_from=tools_to_call_from,
            **kwargs,
        )
        # Override the OpenAI schema for VLLM compatibility
        guided_options_request = {"guided_json": response_format["json_schema"]["schema"]} if response_format else None

        messages = completion_kwargs.pop("messages")
        prepared_stop_sequences = completion_kwargs.pop("stop", [])
        tools = completion_kwargs.pop("tools", None)
        completion_kwargs.pop("tool_choice", None)

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tools=tools,
            add_generation_prompt=True,
            tokenize=False,
        )

        if self.sampling_params is None:
            sampling_params = SamplingParams(
                n=kwargs.get("n", 1),
                temperature=kwargs.get("temperature", 0.0),
                max_tokens=kwargs.get("max_tokens", 2048),
                stop=prepared_stop_sequences,
            )
        else:
            sampling_params = self.sampling_params

        out = self.model.generate(
            prompt,
            sampling_params=sampling_params,
            guided_options_request=guided_options_request,
        )

        output_text = out[0].outputs[0].text
        self._last_input_token_count = len(out[0].prompt_token_ids)
        self._last_output_token_count = len(out[0].outputs[0].token_ids)
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=output_text,
            raw={"out": output_text, "completion_kwargs": completion_kwargs},
            token_usage=TokenUsage(
                input_tokens=len(out[0].prompt_token_ids),
                output_tokens=len(out[0].outputs[0].token_ids),
            ),
        )
