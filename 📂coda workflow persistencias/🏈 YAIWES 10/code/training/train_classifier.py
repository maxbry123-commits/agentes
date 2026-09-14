"""Fine-tune Mistral 7B for the Classifier Agent using Unsloth + QLoRA.

Base: mistralai/Mistral-7B-Instruct-v0.3
Dataset: data/classifier/classifier_train.jsonl
Target: >85% CVE accuracy, CVSS MAE <0.5, >90% FP recall
"""

def train_classifier_model(
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.3",
    dataset_path: str = None,
    output_dir: str = "models/classifier-agent",
    epochs: int = 2,
    lora_r: int = 64,
    lora_alpha: int = 16,
):
    print(f"=== Classifier Agent Fine-Tuning ===")
    print(f"Base: {base_model}")
    print(f"LoRA: r={lora_r}, alpha={lora_alpha}, epochs={epochs}")

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import load_dataset
    except ImportError:
        print("Install: pip install unsloth trl datasets transformers")
        return

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model, max_seq_length=4096, load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model, r=lora_r, lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0, bias="none", use_gradient_checkpointing="unsloth",
    )

    import os
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "classifier", "classifier_train.jsonl")

    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def format_prompt(ex):
        return f"### Instruction:\n{ex['instruction']}\n\n### Input:\n{ex['input']}\n\n### Response:\n{ex['output']}"

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=dataset,
        args=TrainingArguments(
            output_dir=output_dir, num_train_epochs=epochs,
            per_device_train_batch_size=4, gradient_accumulation_steps=8,
            learning_rate=2e-4, warmup_steps=100, save_steps=500,
            fp16=True, report_to="none",
        ),
        formatting_func=format_prompt, max_seq_length=4096,
    )

    trainer.train()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")


if __name__ == "__main__":
    train_classifier_model()
