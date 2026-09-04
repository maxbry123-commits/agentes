from functools import partial

from datasets import concatenate_datasets, load_dataset

from dcft.data_strategies.Stratos.convert import map_to_share_gpt

math_dataset_unverified = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated", split="train"
)
code_dataset_unverified = load_dataset(
    "mlfoundations-dev/code_stratos_scale_rejection_sampled_test", split="train"
)
science_and_puzzle_dataset_unverified = load_dataset(
    "mlfoundations-dev/science_and_puzzle_stratos_scale_annotated_with_answers",
    split="train",
)

math_dataset_unverified = math_dataset_unverified.map(
    partial(map_to_share_gpt, user_column="problem", math=True)
)
code_dataset_unverified = code_dataset_unverified.map(
    partial(map_to_share_gpt, user_column="prompt_formatted", code=True)
)
science_and_puzzle_dataset_unverified = science_and_puzzle_dataset_unverified.map(
    partial(map_to_share_gpt, user_column="problem")
)

math_dataset_verified = math_dataset_unverified.filter(lambda x: x["correct"])
code_dataset_verified = code_dataset_unverified.filter(lambda x: x["correctness"])
science_and_puzzle_dataset_verified = science_and_puzzle_dataset_unverified  # We didn't do any verification on science. camel can't be verified and we didn't verify puzzle

# math_dataset_unverified.push_to_hub("mlfoundations-dev/math-stratos-unverified-with-conversations")
# code_dataset_unverified.push_to_hub("mlfoundations-dev/code-stratos-unverified-with-conversations")
# science_and_puzzle_dataset_unverified.push_to_hub("mlfoundations-dev/science-and-puzzle-stratos-unverified-with-conversations")

# # https://docs.google.com/document/d/1q_XLdz0hrnG9kBwebZ-IFqj8-ZYnCwxYlxOqod_bxB8/edit?tab=t.ys2ejo8rluh


for scale in [0.125, 0.25, 0.5, 1]:
    # NOTE: to keep the experiment compute controlled, I am using the subsampling scale on the length of the verified dataset,
    # even for the unverified dataset. samples = int(len(dataset_verified) * scale)

    math_unverified_scaled = math_dataset_unverified.shuffle(seed=42).take(
        int(len(math_dataset_verified) * scale)
    )
    code_unverified_scaled = code_dataset_unverified.shuffle(seed=42).take(
        int(len(code_dataset_verified) * scale)
    )
    science_and_puzzle_unverified_scaled = (
        science_and_puzzle_dataset_unverified.shuffle(seed=42).take(
            int(len(science_and_puzzle_dataset_verified) * scale)
        )
    )

    math_verified_scaled = math_dataset_verified.shuffle(seed=42).take(
        int(len(math_dataset_verified) * scale)
    )
    code_verified_scaled = code_dataset_verified.shuffle(seed=42).take(
        int(len(code_dataset_verified) * scale)
    )
    science_and_puzzle_verified_scaled = science_and_puzzle_dataset_verified.shuffle(
        seed=42
    ).take(int(len(science_and_puzzle_dataset_verified) * scale))

    unverified_mix_scaled = concatenate_datasets(
        [
            math_unverified_scaled,
            code_unverified_scaled,
            science_and_puzzle_unverified_scaled,
        ]
    )
    verified_mix_scaled = concatenate_datasets(
        [math_verified_scaled, code_verified_scaled, science_and_puzzle_verified_scaled]
    )

    math_unverified_scaled.push_to_hub(
        "mlfoundations-dev/math-stratos-unverified-scaled-{}".format(scale)
    )
    code_unverified_scaled.push_to_hub(
        "mlfoundations-dev/code-stratos-unverified-scaled-{}".format(scale)
    )
    science_and_puzzle_unverified_scaled.push_to_hub(
        "mlfoundations-dev/science-and-puzzle-stratos-unverified-scaled-{}".format(
            scale
        )
    )

    math_verified_scaled.push_to_hub(
        "mlfoundations-dev/math-stratos-verified-scaled-{}".format(scale)
    )
    code_verified_scaled.push_to_hub(
        "mlfoundations-dev/code-stratos-verified-scaled-{}".format(scale)
    )
    science_and_puzzle_verified_scaled.push_to_hub(
        "mlfoundations-dev/science-and-puzzle-stratos-verified-scaled-{}".format(scale)
    )

    unverified_mix_scaled.push_to_hub(
        "mlfoundations-dev/stratos-unverified-mix-scaled-{}".format(scale)
    )
    verified_mix_scaled.push_to_hub(
        "mlfoundations-dev/stratos-verified-mix-scaled-{}".format(scale)
    )

for start in [
    "mlfoundations-dev/",
    "https://huggingface.co/datasets/mlfoundations-dev/",
]:
    for type in ["verified", "unverified"]:
        for scale in [0.125, 0.25, 0.5, 1]:
            print(f"{start}stratos-{type}-mix-scaled-{scale}")
        print("")

    for prefix in ["math-", "code-", "science-and-puzzle-"]:
        for type in ["verified", "unverified"]:
            for scale in [0.125, 0.25, 0.5, 1]:
                print(f"{start}{prefix}stratos-{type}-scaled-{scale}")
            print("")
