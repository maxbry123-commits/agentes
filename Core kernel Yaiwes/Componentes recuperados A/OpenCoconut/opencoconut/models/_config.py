import os
import json
from typing import Dict
from dataclasses import dataclass, field, asdict
from transformers import PreTrainedTokenizer
from transformers.utils.hub import PushToHubMixin, cached_file


@dataclass
class CoconutConfig(PushToHubMixin):
    stages: int = field(default=4)
    continuous_thoughts: int = field(default=2)
    pad_token_id: int = field(default=None)
    bot: str = field(default="<bot>")
    eot: str = field(default="<eot>")
    bot_id: int = field(default=None)
    eot_id: int = field(default=None)
    mix_prob: float = field(default=0.3)

    @classmethod
    def from_dict(cls, config: Dict = {}):
        if not config:
            config = cls()
        else:
            config = cls(**config)
        return config

    @classmethod
    def from_tokenizer(cls, tokenizer: PreTrainedTokenizer, **kwargs):
        """
        Create a CoconutConfig instance from a tokenizer, automatically setting token IDs.
        """
        bot = kwargs.pop('bot', '<bot>')
        eot = kwargs.pop('eot', '<eot>')
        
        # Add special tokens if they don't exist
        if bot not in tokenizer.additional_special_tokens:
            tokenizer.add_special_tokens({"additional_special_tokens": [bot, eot]})
        
        config_dict = {
            'bot': bot,
            'eot': eot,
            'bot_id': tokenizer.convert_tokens_to_ids(bot),
            'eot_id': tokenizer.convert_tokens_to_ids(eot),
            'pad_token_id': tokenizer.pad_token_id,
            **kwargs
        }
        
        return cls(**config_dict)

    @classmethod
    def from_pretrained(cls, save_dir: str, config_file_name="config.json", **kwargs):
        cache_dir = kwargs.pop("cache_dir", None)
        force_download = kwargs.pop("force_download", False)
        proxies = kwargs.pop("proxies", None)
        local_files_only = kwargs.pop("local_files_only", False)
        use_auth_token = kwargs.pop("use_auth_token", None)
        revision = kwargs.pop("revision", None)
        subfolder = kwargs.pop("subfolder", None)
        commit_hash = kwargs.pop("_commit_hash", None)

        if os.path.isdir(save_dir):  # Local
            resolved_config_file = os.path.join(save_dir, config_file_name)
        else:  # Remote
            resolved_config_file = cached_file(
                save_dir,
                config_file_name,
                cache_dir=cache_dir,
                force_download=force_download,
                proxies=proxies,
                use_auth_token=use_auth_token,
                revision=revision,
                local_files_only=local_files_only,
                subfolder=subfolder,
                _raise_exceptions_for_missing_entries=False,
                _raise_exceptions_for_connection_errors=False,
                _commit_hash=commit_hash,
            )

        config = None
        if os.path.exists(resolved_config_file):
            with open(resolved_config_file, "r", encoding="utf-8") as file:
                loaded_config = json.loads(file.read())

            config = loaded_config.get("coconut_config")

            if config is not None:
                config = cls(**config)

        if config is None:
            raise AttributeError("No coconut_config attribute found in config.json.")

        return config

    def to_dict(self):
        return asdict(self)

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4)