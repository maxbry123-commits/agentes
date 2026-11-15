"""Fine-tune Qwen 2.5 7B for the Recon Agent using Unsloth + QLoRA.

Base: Qwen/Qwen2.5-7B-Instruct
Dataset: data/recon/recon_train.jsonl (45k train / 4k val)
Target: >95% valid AttackSurface JSON on test set
"""

import os
import json

# Unsloth for 2x faster fine-tuning with 70% less VRAM
# pip install unsloth

def train_recon_model(
    base_model: str = "Qwen/Qwen2.5-7B-Instruct",
    dataset_path: str = None,
    output_dir: str = "models/recon-agent",
    epochs: int = 3,
    batch_size: int = 4,
    grad_accum: int = 8,
    lora_r: int = 64,
    lora_alpha: int = 16,
    learning_rate: float = 2e-4,
    seed: int = 42,
):
    """Fine-tune the recon agent model."""

    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "recon", "recon_train.jsonl")

    print(f"=== Recon Agent Fine-Tuning ===")
    print(f"Base model: {base_model}")
    print(f"Dataset: {dataset_path}")
    print(f"Config: epochs={epochs}, batch={batch_size}, grad_accum={grad_accum}")
    print(f"LoRA: r={lora_r}, alpha={lora_alpha}")
    print()

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import load_dataset
    except ImportError:
        print("Required packages not installed. Run:")
        print("  pip install unsloth trl datasets transformers")
        print()
        print("For GPU training, use RunPod or Lambda Labs with A100.")
        return

    # Load model with Unsloth (2x faster, 70% less VRAM)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=4096,
        dtype=None,  # auto-detect
        load_in_4bit=True,  # QLoRA
    )

    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=seed,
    )

    # Load dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # Format for training
    def format_prompt(example):
        return f"""### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""

    # Training arguments
    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        save_total_limit=3,
        fp16=True,
        seed=seed,
        report_to="none",
    )

    # Train
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=args,
        formatting_func=format_prompt,
        max_seq_length=4096,
    )

    print("Starting training...")
    trainer.train()

    # Save
    print(f"Saving model to {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("Done! Push to HuggingFace with:")
    print(f"  huggingface-cli upload ArmurAI/recon-agent-qwen2.5-7b {output_dir}")


if __name__ == "__main__":
    train_recon_model()
