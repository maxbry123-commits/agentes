from datasets import Sequence, Value, concatenate_datasets, load_dataset


def combine_code_datasets(datasets_dict):
    apps = datasets_dict["apps"]
    code_contests = datasets_dict["code_contests"]
    taco = datasets_dict["TACO"]
    codeforces = datasets_dict["Codeforces-Python-Submissions"]
    # Standardize schema for all datasets
    apps = apps.map(
        lambda x: {
            "language": (
                [x["language"]]
                if isinstance(x["language"], str)
                else x["language"]["language"]
            )
        }
    )

    taco = taco.map(
        lambda x: {
            "language": (
                [x["language"]] if isinstance(x["language"], str) else x["language"]
            )
        }
    )
    code_contests = code_contests.map(
        lambda x: {
            "language": (
                [x["language"]] if isinstance(x["language"], str) else x["language"]
            )
        }
    )
    codeforces = codeforces.map(
        lambda x: {
            "language": (
                [x["language"]] if isinstance(x["language"], str) else x["language"]
            )
        }
    )
    # codeforces = codeforces.remove_columns(["__index_level_0__"])
    codeforces = codeforces.remove_columns(["solutions"])
    apps = apps.remove_columns(["solutions"])
    taco = taco.remove_columns(["solutions"])
    code_contests = code_contests.remove_columns(["solutions"])
    code_contests = code_contests.cast_column("difficulty", Value("string"))
    code_contests = code_contests.cast_column("source", Value("string"))

    new_features = code_contests.features
    print(new_features)
    new_features["difficulty"] = Value("string")
    new_features["language"] = Sequence(Value("string"))
    code_contests = code_contests.cast(new_features)
    apps = apps.cast(new_features)
    taco = taco.cast(new_features)
    codeforces = codeforces.cast(new_features)

    code_contests = code_contests.add_column(
        "subset", ["code_contests"] * len(code_contests)
    )
    apps = apps.add_column("subset", ["apps"] * len(apps))
    taco = taco.add_column("subset", ["taco"] * len(taco))
    codeforces = codeforces.add_column("subset", ["codeforces"] * len(codeforces))

    # Concatenate all datasets
    code_stratos_scale = concatenate_datasets([code_contests, apps, taco, codeforces])

    print(f"Total examples: {len(code_stratos_scale)}")

    return code_stratos_scale


if __name__ == "__main__":
    code_contests = load_dataset(
        "mlfoundations-dev/code_contests_processed", split="train"
    )
    apps = load_dataset("mlfoundations-dev/apps_processed", split="train")
    taco = load_dataset("mlfoundations-dev/TACO_processed", split="train")
    codeforces = load_dataset(
        "mlfoundations-dev/Codeforces-Python-Submissions_processed", split="train"
    )
    datasets_dict = {
        "code_contests": code_contests,
        "apps": apps,
        "TACO": taco,
        "Codeforces-Python-Submissions": codeforces,
    }
    code_stratos_scale = combine_code_datasets(datasets_dict)
    code_stratos_scale.push_to_hub(
        "mlfoundations-dev/code_stratos_scale_pre_decontamination"
    )
