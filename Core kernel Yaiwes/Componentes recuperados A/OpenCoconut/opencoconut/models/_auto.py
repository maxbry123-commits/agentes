from typing import Union
from transformers import AutoConfig, PreTrainedModel
from opencoconut.models import *

COCONUT_CAUSAL_LM_MODEL_MAP = {
    "qwen2": CoconutQwen2ForCausalLM,
}


def check_and_get_model_type(model_name_or_path: str, **config_init_kwargs) -> str:
    config = AutoConfig.from_pretrained(model_name_or_path, **config_init_kwargs)
    if config.model_type not in COCONUT_CAUSAL_LM_MODEL_MAP.keys():
        raise TypeError(f"{config.model_type} isn't supported yet.")
    model_type = config.model_type
    return model_type


class AutoCoconutForCausalLM:
    def __init__(self):
        raise EnvironmentError(
            "You must instantiate AutoCoconutForCausalLM with\n"
            "AutoCoconutForCausalLM.from_pretrained"
        )

    @classmethod
    def from_pretrained(
        cls,
        model_path,
        config: Union[CoconutConfig] = None,
        config_init_kwargs={},
        *args,
        **kwargs,
    ) -> PreTrainedModel:
        model_type = check_and_get_model_type(
            model_path, trust_remote_code=True, **config_init_kwargs
        )

        if config is None:
            config = CoconutConfig.from_pretrained(model_path)

        model_config = AutoConfig.from_pretrained(model_path, **config_init_kwargs)
        model_config.coconut_config = config.to_dict()

        return COCONUT_CAUSAL_LM_MODEL_MAP[model_type].from_pretrained(
            model_path,
            config=model_config,
            *args,
            **kwargs,
        )