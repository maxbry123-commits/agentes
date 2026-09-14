#!/usr/bin/env python3
"""
Concise prompt preprocessing using Hugging Face AutoTokenizer.
Replaces hand-written tokenizers and chat formatters with standard HF implementation.
"""

import argparse
from typing import List, Literal, Optional

from transformers import AutoTokenizer

RESPOND_MODE = Literal["chat", "completion"]

# Model configurations
MODEL_CONFIGS = {
    "llama2": {
        "model_name": "meta-llama/Llama-2-7b-chat-hf",
        "max_tokens": 4096,
    },
    "llama3": {
        "model_name": "meta-llama/Llama-3.2-3B-Instruct",
        "max_tokens": 128000,
    },
}


class Tokenizer:
    def __init__(self, llm_type: str, model_path: Optional[str] = None):
        """Initialize the preprocessor with HuggingFace tokenizer.

        Args:
            llm_type: Type of LLM (llama2, llama3)
            model_path: Optional custom model path
        """
        if llm_type not in MODEL_CONFIGS:
            supported = ", ".join(MODEL_CONFIGS.keys())
            raise ValueError(f"Unsupported LLM type: {llm_type}. Supported: {supported}")

        self.llm_type = llm_type
        self.config = MODEL_CONFIGS[llm_type]
        self.max_tokens = self.config["max_tokens"]

        # Initialize tokenizer
        model_name = model_path if model_path else self.config["model_name"]
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side="left"
        )

        # Ensure pad token is set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def apply_chat_template(self, messages: List[dict], tokenize: bool = False, add_generation_prompt: bool = True) -> str:
        """Apply chat template to messages."""
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=tokenize,
            add_generation_prompt=add_generation_prompt
        )

    def encode_chat(
        self,
        messages: List[dict],
    ) -> List[int]:
        """Encode a string into token IDs.

        Args:
            prompt: Input text to tokenize
            mode: Either 'chat' or 'completion'
            system_prompt: Optional system message for chat mode

        Returns:
            List of token IDs
        """
        formatted_prompt = self.apply_chat_template(messages)
        tokens = self.tokenizer.encode(
            formatted_prompt, add_special_tokens=True)

        return tokens

    def encode_completion(
        self,
        prompt: str,
    ) -> List[int]:
        """Encode a string into token IDs."""
        tokens = self.tokenizer.encode(prompt, add_special_tokens=True)
        return tokens

    def decode(self, tokens: List[int], skip_special_tokens: bool = True) -> str:
        """Decode token IDs back to text."""
        return self.tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens)

    def is_end_of_generation(self, token_id: int) -> bool:
        """Check if a token ID represents the end of generation.

        Args:
            token_id: Token ID to check

        Returns:
            True if token indicates end of generation, False otherwise
        """
        # Check for standard EOS token
        if token_id == self.tokenizer.eos_token_id:
            return True

        # Check for model-specific end tokens
        special_tokens = getattr(self.tokenizer, 'special_tokens_map', {})

        # Common end-of-generation tokens
        end_tokens = []

        # Add EOS token variants
        if 'eos_token' in special_tokens:
            eos_token = special_tokens['eos_token']
            if isinstance(eos_token, str):
                eos_id = self.tokenizer.convert_tokens_to_ids(eos_token)
                if eos_id is not None:
                    end_tokens.append(eos_id)

        # For Llama 3+ models, check for specific end tokens
        if self.llm_type.startswith('llama3'):
            # Llama 3 uses <|eot_id|> as end of turn token
            eot_tokens = ['<|eot_id|>', '<|end_of_text|>']
            for token in eot_tokens:
                token_id_mapped = self.tokenizer.convert_tokens_to_ids(token)
                if token_id_mapped is not None and token_id_mapped != self.tokenizer.unk_token_id:
                    end_tokens.append(token_id_mapped)

        # Check if token_id matches any end tokens
        return token_id in end_tokens

    def get_end_tokens(self) -> List[int]:
        """Get all token IDs that represent end of generation.

        Returns:
            List of token IDs that indicate end of generation
        """
        end_tokens = []

        # Add EOS token
        if self.tokenizer.eos_token_id is not None:
            end_tokens.append(self.tokenizer.eos_token_id)

        # Add model-specific end tokens
        if self.llm_type.startswith('llama3'):
            eot_tokens = ['<|eot_id|>', '<|end_of_text|>']
            for token in eot_tokens:
                token_id = self.tokenizer.convert_tokens_to_ids(token)
                if token_id is not None and token_id != self.tokenizer.unk_token_id:
                    end_tokens.append(token_id)

        return list(set(end_tokens))  # Remove duplicates

    def save_prompt_tokens(
        self,
        tokens: List[int],
        output_path: str,
    ) -> None:
        # Truncate if exceeds max tokens
        original_length = len(tokens)
        if original_length > self.max_tokens:
            tokens = tokens[:self.max_tokens]
            print(f"Original token length: {original_length}, truncated to {self.max_tokens}")
        else:
            print(f"Output token length: {original_length}")

        # Save tokens to file
        with open(output_path, "w") as f:
            f.write(" ".join(map(str, tokens)))

        print(f"Token IDs saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess prompts using HuggingFace AutoTokenizer"
    )
    parser.add_argument(
        "-m", "--llm",
        type=str,
        default="llama3",
        choices=list(MODEL_CONFIGS.keys()),
        help="Type of LLM model"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Custom model path (default: use predefined model)"
    )
    parser.add_argument(
        "--mode",
        default="chat",
        choices=["chat", "completion"],
        help="Encoding mode"
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        help="Prompt string to tokenize"
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        help="Path to prompt file"
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        help="System prompt for chat mode"
    )
    parser.add_argument(
        "-o", "--output-path",
        type=str,
        default="input.prompt",
        help="Output path for token IDs"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - show encoding/decoding without saving"
    )

    args = parser.parse_args()

    # Initialize preprocessor
    preprocessor = Tokenizer(args.llm, args.model_path)

    # Get input prompt
    if args.prompt:
        input_str = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, "r") as f:
            input_str = f.read()
    else:
        input_str = input("Enter a prompt string: ")

    if args.test:
        # Test mode - show encoding and decoding
        if args.mode == "chat":
            # For chat mode, we need to construct messages
            messages = []
            if args.system_prompt:
                messages.append(
                    {"role": "system", "content": args.system_prompt})
            messages.append({"role": "user", "content": input_str})
            tokens = preprocessor.encode_chat(messages)
        else:
            # For completion mode
            tokens = preprocessor.encode_completion(input_str)

        print(f"Original input string:\n{input_str}")
        print(f"***** Length of encoded tokens: {len(tokens)} *****")
        decoded_str = preprocessor.decode(tokens, skip_special_tokens=False)
        print(f"Decoded string:\n{decoded_str}")

        # Show end-of-generation tokens info
        end_tokens = preprocessor.get_end_tokens()
        print(f"\nEnd-of-generation token IDs: {end_tokens}")

        # Check if any tokens in the prompt are end tokens
        end_token_found = False
        for i, token_id in enumerate(tokens):
            if preprocessor.is_end_of_generation(token_id):
                print(
                    f"Found end-of-generation token at position {i}: {token_id}")
                end_token_found = True

        if not end_token_found:
            print("No end-of-generation tokens found in the encoded prompt.")
    else:
        # Save tokens to file
        if args.mode == "chat":
            # For chat mode, we need to construct messages
            messages = []
            if args.system_prompt:
                messages.append(
                    {"role": "system", "content": args.system_prompt})
            messages.append({"role": "user", "content": input_str})
            tokens = preprocessor.encode_chat(messages)
        else:
            # For completion mode
            tokens = preprocessor.encode_completion(input_str)

        preprocessor.save_prompt_tokens(tokens, args.output_path)


if __name__ == "__main__":
    main()
