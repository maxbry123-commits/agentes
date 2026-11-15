# Description: This script is used to construct a positive test set for a WebInstruct Phase 1 classifier
# Text each text field in the dataset is classified as positive or negative with gpt4-mini

# Batches are submitted and retrieved following https://platform.openai.com/docs/guides/batch/getting-started

# usage:
#   Submit a batch request, to classify number-examples from the dataset:
#       python construct_test_set_stage1.py --submit --dataset mlfoundations-dev/webinstruct_v1_beta_stage_3_gpt-4o-mini --number-examples 5000
#   Retrieve the batch results, and save them to the output file:
#       python construct_test_set_stage1.py --retrieve batch_67238f2bfe1081908bfcb7e20b126a94 --output-file-prefix fasttext_examples
#
# An openai account is required, and the API key should be set as an environment variable.
# export OPENAI_API_KEY="your-api-key"

import argparse
import json
import logging

from datasets import load_dataset
from openai import OpenAI


def print_dataset_information(dataset):
    urls = {}
    for entry in dataset["train"]:
        url = entry["url"]
        url = url.split("//")[-1].split("/")[0]
        # remove www if applicable
        if url.startswith("www."):
            url = url[4:]
        if url in urls:
            urls[url] += 1
        else:
            urls[url] = 1

    # sort the urls by frequency
    urls = dict(sorted(urls.items(), key=lambda item: item[1], reverse=True))

    # print the number of unique urls
    print(f"Number of unique urls: {len(urls)}")
    # print the total number of urls
    print(f"Total number of urls: {sum(urls.values())}")

    # print the 25 most frequent urls
    print("25 most frequent urls:")
    for url, count in list(urls.items())[:25]:
        print(f"\t{url}: {count}")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Rewriting script.")

    # Add arguments
    parser.add_argument(
        "--retrieve", type=str, required=False, help="Batch id to retrieve"
    )
    parser.add_argument(
        "--number-examples",
        type=int,
        default=150,
        required=False,
        help="Number of examples to retrieve",
    )
    parser.add_argument(
        "--submit", action="store_true", help="Generate and submit a batch request"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mlfoundations-dev/webinstruct_v1_beta_stage_3_gpt-4o-mini",
        required=False,
        help="Dataset name",
    )
    parser.add_argument(
        "--output-file-prefix",
        type=str,
        default="fasttext_examples",
        required=False,
        help="Path to the prefix to write positive and negative jsonl examples to",
    )

    # Parse the arguments
    args = parser.parse_args()
    logging.info(f"Arguments received: {args}")

    prompt = "Check whether the following text contains self-contained (i.e., sufficient context to answer is given and the text does not refer to a figure, table, or any other exhibit) instruction-following data about math, science, engineering, or humanities, such as an instruction and completion of the instruction, a question and answer pair, a question required reasoning, or an educational question. Justify and then conclude your answer with Yes or No. Choose No if the text is an advertisement."

    if args.submit:
        ### generate ..._batch.jsonl file for the batch request

        # 1. Load the dataset & print some information

        dataset_name = (
            args.dataset
        )  # "mlfoundations-dev/webinstruct_v1_beta_stage_3_gpt-4o-mini"
        dataset = load_dataset(dataset_name)
        dataset = dataset.shuffle(seed=42)
        print_dataset_information(dataset)

        # 2. Write the batch input file

        batch_file_name = "queries_batch.jsonl"
        with open(batch_file_name, "w") as file:
            for i, entry in enumerate(dataset["train"]):
                text = entry["text"]
                json_data = json.dumps(
                    {
                        "custom_id": f"request-{i}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": "gpt-4o-mini",
                            #'messages': [{'role': 'system', 'content': "You are a helpful assistant"},
                            #            {"role": "user", "content": prompt + text}],
                            "messages": [
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": text},
                            ],
                            "max_tokens": 2048,
                        },
                    }
                )

                # Write without adding newline at the end for the last item
                if i < args.number_examples - 1:
                    file.write(json_data + "\n")  # Add newline between entries
                elif i == args.number_examples - 1:
                    file.write(json_data)  # No newline for the last entry
                else:
                    break

        # 3. upload batch input file
        client = OpenAI()

        batch_input_file = client.files.create(
            file=open(batch_file_name, "rb"), purpose="batch"
        )

        batch_input_file_id = batch_input_file.id

        batch = client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "Classify texts in " + args.dataset},
        )
        logging.info(f"submitted batch request with id {batch.id}")

    elif args.retrieve:
        # 1. check batch status
        client = OpenAI()
        batch = client.batches.retrieve(args.retrieve)
        logging.info("Status: %s", batch.status)
        logging.info("Output file id: %s", batch.output_file_id)
        logging.info("Request counts: %s", batch.request_counts)

        # 2. retrieving the results
        if batch.status == "completed":
            # 4. downloading the batch output file
            client = OpenAI()
            file_response = client.files.content(batch.output_file_id)
            # file_response is the content of the JSONL file, which is iterable

            dataset_name = (
                args.dataset
            )  # "mlfoundations-dev/webinstruct_v1_beta_stage_3_gpt-4o-mini"
            dataset = load_dataset(dataset_name)
            dataset = dataset.shuffle(seed=42)

            # append output to jsonl file
            with open(
                args.output_file_prefix + "_positive.txt", "w"
            ) as file_positive, open(
                args.output_file_prefix + "_negative.txt", "w"
            ) as file_negative:
                # iterate through the dataset and the file_response, stop when file_response is exhausted
                ctr_positive = 0
                ctr_negative = 0
                for i, (line, entry) in enumerate(
                    zip(file_response.text.split("\n"), dataset["train"])
                ):
                    if (
                        line.strip()
                    ):  # Check if the line has content to avoid empty lines
                        data = json.loads(line)

                        response = data["response"]["body"]["choices"][0]["message"][
                            "content"
                        ]
                        response_end = response[-10:]
                        custom_id = data["custom_id"]
                        # extract number from custom_id
                        idx = int(custom_id.split("-")[-1])
                        # check if idx is equal to i
                        assert idx == i, f"idx: {idx}, i: {i}"

                        text = entry["text"]

                        if "Yes" in response and "No" not in response_end:
                            ctr_positive += 1
                            file_positive.write(
                                f"__label__positive {json.dumps(text)[1:-1]}\n"
                            )
                        if "No" in response and "Yes" not in response_end:
                            ctr_negative += 1
                            file_negative.write(
                                f"__label__negative {json.dumps(text)[1:-1]}\n"
                            )
                        # else do nothing, since either No or both Yes and No or neither are present
                # log number of positive examples
                logging.info(
                    f"Number of positive and negative examples: {ctr_positive}, {ctr_negative}"
                )


# Entry point of the script
if __name__ == "__main__":
    main()
