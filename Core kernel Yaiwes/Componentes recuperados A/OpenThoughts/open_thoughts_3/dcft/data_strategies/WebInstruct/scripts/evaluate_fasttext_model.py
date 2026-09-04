import argparse
import json
import logging
import os
import re

import fasttext
from huggingface_hub import hf_hub_download


def clean_text(text):
    # Remove extra whitespace and newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove any non-printable characters
    text = "".join(char for char in text if char.isprintable())
    return text


def evaluate_model_on_testset(model, test_set_file):
    # Initialize counters for accuracy evaluation (optional)
    total = 0
    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0

    # Process each line in the file
    with open(test_set_file, "r") as f:
        for line in f:
            # Split the line into label and text
            parts = line.strip().split(" ", 1)
            true_label = parts[0]  # Original label (e.g., __label__positive)
            text = parts[1] if len(parts) > 1 else ""  # The text to classify
            decoded_text = json.loads(f'"{text}"')
            cleaned_text = clean_text(decoded_text)

            predicted_label, _ = model.predict(cleaned_text)

            if (
                predicted_label[0] == "__label__QA_doc"
                and true_label == "__label__positive"
            ):
                true_positive += 1
            if (
                predicted_label[0] == "__label__QA_doc"
                and true_label == "__label__negative"
            ):
                false_positive += 1
            if (
                predicted_label[0] == "__label__Not_QA_doc"
                and true_label == "__label__positive"
            ):
                false_negative += 1
            if (
                predicted_label[0] == "__label__Not_QA_doc"
                and true_label == "__label__negative"
            ):
                true_negative += 1
            total += 1

    test_set_file_basename = os.path.basename(test_set_file)
    print("Evaluating the model on: ", test_set_file_basename)
    print(f"\tTrue positive: {true_positive/total:.2%}")
    print(f"\tFalse positive: {false_positive/total:.2%}")
    print(f"\tTrue negative: {true_negative/total:.2%}")
    print(f"\tFalse negative: {false_negative/total:.2%}")
    print(f"\tAccuracy: {(true_positive + true_negative) / total:.2%}")

    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    f1 = 2 * precision * recall / (precision + recall)
    print(f"\tPrecision: {precision:.2%}")
    print(f"\tRecall: {recall:.2%}")
    print(f"\tF1 score: {f1:.2%}")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Model evaluation script.")

    # Add arguments
    parser.add_argument(
        "--repo-id",
        type=str,
        required=True,
        help="Repository ID where model.bin is stored",
    )
    parser.add_argument(
        "--use-auth-token", type=str, required=True, help="Hugging Face API token"
    )
    parser.add_argument(
        "--model-filename",
        type=str,
        default="model.bin",
        required=False,
        help="Fasttext model repository filename",
    )

    # Parse the arguments
    args = parser.parse_args()
    logging.info(f"Arguments received: {args}")

    eval_set_std_path = hf_hub_download(
        repo_id="mlfoundations-dev/fasttext_test_EDUvsRW",
        repo_type="dataset",
        filename="fasttext_test_EDUvsRW.txt",
        use_auth_token=args.use_auth_token,
    )

    eval_set_difficult_path = hf_hub_download(
        repo_id="mlfoundations-dev/fasttext_test_EDUvsRW",
        repo_type="dataset",
        filename="fasttext_test_EDUvsRW_difficult.txt",
        use_auth_token=args.use_auth_token,
    )

    model_path = hf_hub_download(
        repo_id=args.repo_id,
        filename=args.model_filename,
        use_auth_token=args.use_auth_token,
    )

    model = fasttext.load_model(model_path)
    print("Evaluating model ", args.repo_id + "/" + args.model_filename)
    evaluate_model_on_testset(model, eval_set_std_path)
    evaluate_model_on_testset(model, eval_set_difficult_path)


# Entry point of the script
if __name__ == "__main__":
    main()
