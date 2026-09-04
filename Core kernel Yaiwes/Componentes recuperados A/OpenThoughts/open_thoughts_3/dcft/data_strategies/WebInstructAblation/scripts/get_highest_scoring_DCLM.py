import argparse
import io
import json
import logging
import os
import random
import time

import ray
import zstandard as zstd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@ray.remote
def sample_from_shard(shard_path, probability_threshold):
    logger.info(f"Processing shard: {shard_path}")

    sampled_lines = []
    ctr = 0
    with open(shard_path, "rb") as shard:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(shard) as decompressed_stream:
            text_stream = io.TextIOWrapper(decompressed_stream, encoding="utf-8")
            for line in text_stream:
                # Decode the line as JSON
                try:
                    data = json.loads(line)
                    # Access the field
                    probability = data[
                        "fasttext_openhermes_reddit_eli5_vs_rw_v2_bigram_200k_train_prob"
                    ]
                    if probability > probability_threshold:
                        sampled_lines.append(data)
                        ctr += 1

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {shard_path}")
                    continue

    # Log the number of lines sampled from the shard
    logger.info(f"Shard {shard_path} sampled {ctr} lines")

    return sampled_lines


def list_all_shards(root_folder):
    shard_paths = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # Assuming each file in the folders is a shard
            shard_paths.append(os.path.join(dirpath, filename))
    return shard_paths


def write_shards(output_shards, sampled_lines, max_lines_per_shard=16384):
    shard_index = 0
    current_shard = []

    for line in sampled_lines:
        current_shard.append(line)
        if len(current_shard) >= max_lines_per_shard:
            # Write the current shard to a file when it reaches max_lines_per_shard
            output_path = f"{output_shards}/shard_{shard_index}.json"
            with open(output_path, "w") as output_file:
                for item in current_shard:
                    output_file.write(json.dumps(item) + "\n")
            shard_index += 1
            current_shard = []  # Reset for the next shard

    # Write any remaining lines that didn’t reach max_lines_per_shard
    if current_shard:
        output_path = f"{output_shards}/shard_{shard_index}.json"
        with open(output_path, "w") as output_file:
            for item in current_shard:
                output_file.write(json.dumps(item) + "\n")


if __name__ == "__main__":
    # Reads jsons in input folder, filters by url, and writes the filtered jsons to the output folder

    # Setup argument parser
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument(
        "--shard-folder", required=True, help="The name of the folder with the jsons."
    )
    parser.add_argument("--output-folder", required=True, help="The output folder.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="The threshold for the FastText classifier.",
    )
    # Parse arguments
    args = parser.parse_args()
    # print the args nicely formated

    logger.info(f"args: {args}")

    # get the file paths in the folder

    input_shards = list_all_shards(args.shard_folder)

    logger.info(f"Number of input shards: {len(input_shards)}")

    # input_shards = input_shards[:100]  # Limit to 4 shards for testing

    ### Process shards

    # Run sampling in parallel across all input shards
    ray.init(log_to_driver=True)
    # ray.init(local_mode=True, include_dashboard=False, num_cpus=64, log_to_driver=True)
    # ray.init(local_mode=True, log_to_driver=True)

    # ray.init(local_mode=True, log_to_driver=True, include_dashboard=False, num_cpus=16)
    logger.info("Ray initalized")
    logger.info(f"Ray resources: {ray.cluster_resources()}")

    sampled_lines = []

    # measure the time it takes to process the shards
    time_start = time.time()

    futures = [
        sample_from_shard.remote(shard, args.threshold) for shard in input_shards
    ]
    sampled_results = ray.get(futures)

    # Flatten all sampled lines from each shard
    for result in sampled_results:
        sampled_lines.extend(result)

    # Shuffle sampled lines to ensure randomness in output shards
    random.shuffle(sampled_lines)

    # Write shards whenever they reach the max_lines_per_shard limit
    write_shards(args.output_folder, sampled_lines)

    time_end = time.time()
    logger.info(f"Processing time: {time_end - time_start}")
