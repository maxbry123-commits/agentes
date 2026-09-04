from datasets import Dataset


def octopack_map(dataset: Dataset) -> Dataset:
    def f(x):
        return {
            "response_seed": x["new_contents"],
            "instruction_seed": x["message"] + "\n\n" + x["old_contents"],
        }

    dataset = dataset.map(f)
    return dataset


def coder_stat_map(dataset: Dataset) -> Dataset:
    def f(x):
        return {
            "response_seed": x["changed_src"],
            "instruction_seed": x["original_status"] + "\n\n" + x["original_src"],
        }

    dataset = dataset.map(f)
    return dataset


def rosetta_map(dataset: Dataset) -> Dataset:
    def f(x):
        language = x["language_url"]
        return {
            "response_seed": "",
            "instruction_seed": f"Give a code snippet in {language}"
            "\n\n" + x["task_description"],
        }

    dataset = dataset.map(f)
    return dataset


def sql_instruct_map(dataset: Dataset) -> Dataset:
    def f(x):
        instruction = x["text"]
        instruction = instruction.replace("[INST]", "")
        instruction = instruction.replace("[/INST]", "")
        return {"instruction_seed": instruction, "response_seed": ""}

    dataset = dataset.map(f)
    return dataset


def react_map(dataset: Dataset) -> Dataset:
    def f(x):
        instruction = x["messages"][1]["content"]
        response = x["messages"][2]["content"]
        return {"instruction_seed": instruction, "response_seed": response}

    dataset = dataset.map(f)
    return dataset


def reflection_map(dataset: Dataset) -> Dataset:
    def f(x):
        instruction = x["messages"][0]["content"][0]["content"]
        response = x["messages"][1]["content"][0]["content"]
        return {"instruction_seed": instruction, "response_seed": response}

    dataset = dataset.map(f)
    return dataset


def sharegpt_instruct_map(dataset: Dataset) -> Dataset:
    def f(x):
        instruction = x["conversations"][0]["value"]
        response = x["conversations"][1]["value"]
        return {"instruction_seed": instruction, "response_seed": response}

    dataset = dataset.map(f)
    return dataset
