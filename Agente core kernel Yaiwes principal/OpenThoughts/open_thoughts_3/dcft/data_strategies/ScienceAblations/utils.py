from datasets import Dataset
import os


def kaggle_llm_science_exam(dataset: Dataset) -> Dataset:
    def f(x):
        x["instruction_seed"] = (
            f"{x['prompt']} \n\n A. {x['A']} \n\n B. {x['B']} \n\n C. {x['C']} \n\n D. {x['D']} \n\n E. {x['E']}"
        )
        return x

    dataset = dataset.map(f, num_proc=os.cpu_count())
    return dataset
