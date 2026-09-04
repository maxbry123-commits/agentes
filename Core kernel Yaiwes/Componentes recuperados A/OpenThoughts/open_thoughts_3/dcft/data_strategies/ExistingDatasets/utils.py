from datasets import Dataset

from dcft.data_strategies.commons import openai_to_sharegpt


def parse_gemma2_ultrafeedback_armorm(dataset: Dataset) -> Dataset:
    def f(row: dict) -> dict:
        row["conversations"] = openai_to_sharegpt(row["chosen"])[:-1]
        row["chosen"] = openai_to_sharegpt(row["chosen"])[-1]
        row["rejected"] = openai_to_sharegpt(row["rejected"])[-1]
        return row

    dataset = dataset.map(f)
    return dataset


def parse_oh_preferences(dataset: Dataset) -> Dataset:
    def filter_preferences(row: dict) -> dict:
        row["conversations"] = [{"from": "human", "value": row["prompt"]}]
        row["chosen"] = {"from": "gpt", "value": row["chosen"][1]["content"]}
        row["rejected"] = {"from": "gpt", "value": row["rejected"][1]["content"]}
        return row

    return dataset.map(filter_preferences)


def reformat_tags(
    dataset: Dataset,
    messages: str,
    role_tag: str,
    content_tag: str,
    user_tag: str,
    assistant_tag: str,
) -> Dataset:
    """
    Rename tags to:
    role_tag = from
    content_tag = value
    user_tag = human
    assistant_tag = gpt
    """

    def _reformat_tags(example):
        conversation = example[messages]
        for i in range(len(conversation)):
            curr_user = conversation[i][role_tag]
            curr_content = conversation[i][content_tag]
            if curr_user == user_tag:
                conversation[i] = {"from": "human", "value": curr_content}
            elif curr_user == assistant_tag:
                conversation[i] = {"from": "gpt", "value": curr_content}
            else:
                conversation[i] = {"from": curr_user, "value": curr_content}
        example[messages] = conversation
        return example

    return dataset.map(_reformat_tags)
