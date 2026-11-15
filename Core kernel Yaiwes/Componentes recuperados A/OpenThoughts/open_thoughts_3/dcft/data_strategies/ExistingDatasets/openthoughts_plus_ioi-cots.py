from datasets import load_dataset, concatenate_datasets

dataset1 = load_dataset("open-r1/ioi-cots")["train"]
dataset2 = load_dataset("mlfoundations-dev/openthoughts_114k_thinkprompt")["train"]

from dcft.data_strategies.commons import change_tags

dataset1 = dataset1.rename_column("messages", "conversations")
dataset1 = change_tags(
    dataset1,
    conversation_column="conversations",
    tags_to_change={
        "user": "human",
        "assistant": "gpt",
    },
    role_tag="role",
    content_tag="content",
)

combined = concatenate_datasets([dataset1, dataset2])
combined = combined.shuffle(seed=42)
combined.push_to_hub("mlfoundations-dev/openthoughts_plus_ioi-cots")
