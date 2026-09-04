import torch
import torch.nn.functional as F
from datasets import Dataset
from transformers import AutoModel, AutoTokenizer


def compute_batch_rewards(
    dataset: Dataset,
    steps_column: str,
    query_column: str,
    model_name: str,
    batch_size: int = 1,
    device: str = "cuda",
):
    """
    Compute reward scores for each step in the dataset using batch processing.

    Args:
        dataset: Dataset object containing the data
        steps_column: Name of the column containing the step-by-step responses
        query_column: Name of the column containing the user queries
        model: The reward model
        tokenizer: The tokenizer
        batch_size: Size of batches for processing
        device: Device to use for computation

    Returns:
        List of lists containing scores for each step in each example
    """
    all_scores = []
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        device_map=device,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    ).eval()
    for i in range(0, len(dataset), batch_size):
        batch = dataset[i : i + batch_size]
        batch_scores = []

        # Process each example in the batch
        batch_messages = []
        for steps, query in zip(batch[steps_column], batch[query_column]):
            # If the steps are already a list, join them with <extra_0>
            if isinstance(steps, list):
                steps_text = "<extra_0>".join(steps) + "<extra_0>"
            else:
                # If it's a string, assume it's already formatted
                steps_text = steps

            messages = [
                {
                    "role": "system",
                    "content": "Please reason step by step, and put your final answer within \\boxed{}.",
                },
                {"role": "user", "content": query},
                {"role": "assistant", "content": steps_text},
            ]
            batch_messages.append(messages)

        # Process each conversation in the batch
        batch_input_ids = []
        for messages in batch_messages:
            conversation_str = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
            input_ids = tokenizer.encode(
                conversation_str,
                return_tensors="pt",
            )
            batch_input_ids.append(input_ids)

        # Pad the sequences to the same length
        max_length = max(ids.size(1) for ids in batch_input_ids)
        padded_input_ids = []
        padded_masks = []

        for input_ids in batch_input_ids:
            padding_length = max_length - input_ids.size(1)
            if padding_length > 0:
                padded = torch.nn.functional.pad(
                    input_ids, (0, padding_length), value=tokenizer.pad_token_id
                )
            else:
                padded = input_ids
            padded_input_ids.append(padded)

        # Stack all padded inputs
        batch_tensor = torch.cat(padded_input_ids, dim=0).to(model.device)

        # Get model outputs
        with torch.no_grad():
            outputs = model(input_ids=batch_tensor)

        # Create token masks for the batch
        step_sep_id = tokenizer.encode("<extra_0>")[0]
        token_masks = batch_tensor == step_sep_id

        # Compute rewards for the batch
        batch_rewards = make_step_rewards(outputs[0], token_masks)
        all_scores.extend(batch_rewards)
    dataset = dataset.add_column("rewards", all_scores)
    return dataset


def make_step_rewards(logits, token_masks):
    probabilities = F.softmax(logits, dim=-1)
    probabilities = probabilities * token_masks.unsqueeze(-1)  # bs, seq_len, num_labels

    all_scores_res = []
    for i in range(probabilities.size(0)):
        sample = probabilities[i]  # seq_len, num_labels
        positive_probs = sample[sample != 0].view(-1, 2)[
            :, 1
        ]  # valid_tokens, num_labels
        non_zero_elements_list = positive_probs.detach().cpu().tolist()
        all_scores_res.append(non_zero_elements_list)
    return all_scores_res


# Example usage:
"""
# Create a sample dataset
data = {
    "steps": [
        ["step1", "step2", "step3"],
        ["step1", "step2", "step3", "step4"],
    ],
    "query": [
        "What is 2+2?",
        "Solve this math problem..."
    ]
}
dataset = Dataset.from_dict(data)

# Compute rewards
rewards = compute_batch_rewards(
    dataset=dataset,
    steps_column="steps",
    query_column="query",
    model=model,
    tokenizer=tokenizer,
    batch_size=2
)
"""
