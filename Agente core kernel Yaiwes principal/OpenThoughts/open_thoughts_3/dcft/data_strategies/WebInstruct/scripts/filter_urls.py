import argparse
import io
import json
import os
import re
import time
from pprint import pprint

import ray
import zstandard as zstd

tld_sites = [
    "coursehero.com",
    "math.stackexchange.com",
    "answers.com",
    "jiskha.com",
    "brainly.com",
    "homework.study.com",
    "answers.everydaycalculation.com",
    "chemath.org",
    "studypool.com",
    "www.chegg.com",
    "weegy.com",
    "gmatclub.com",
    "www.khanacademy.org",
    "brainmass.com",
    "physicsforums.com",
    "sharemylesson.com",
    "transtutors.com",
    "proofreading.org",
    "enotes.com",
    "cs.stackexchange.com",
    "socratic.org",
    "physics.stackexchange.com",
    "www.indiabix.com",
    "chemistry.stackexchange.com",
    "biology.stackexchange.com",
]

tld_set = set(tld_sites)


@ray.remote
def process_shard(shard_path, output_folder):
    print("Processing shard:", shard_path)

    tld_count = {tld: 0 for tld in tld_sites}

    # construct output_file name as dirname/processed/00000687.jsonl
    # folder_path = os.path.dirname(shard_path)
    file_name = os.path.basename(shard_path)
    match = re.search(r"(\d+)", file_name)
    shard_number = match.group()
    # new_folder = os.path.join(folder_path, "processed")
    output_file = os.path.join(output_folder, f"{shard_number}.jsonl")
    print("Writing to:", output_file)

    with open(shard_path, "rb") as compressed_file, open(output_file, "w") as out_file:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(compressed_file) as decompressed_stream:
            text_stream = io.TextIOWrapper(decompressed_stream, encoding="utf-8")
            for line in text_stream:
                # Decode the line as JSON

                try:
                    json_obj = json.loads(line)
                    url = json_obj["metadata"]["WARC-Target-URI"]
                    tld = url.split("//")[-1].split("/")[0]
                    if tld in tld_set:
                        tld_count[tld] += 1
                        # create a new entry for a new dataset
                        new_entry = {"text": json_obj["text"], "url": url}
                        # add to out_file
                        out_file.write(json.dumps(new_entry) + "\n")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {shard_path}")
                    continue

    return tld_count


if __name__ == "__main__":
    # Reads jsons in input folder, filters by url, and writes the filtered jsons to the output folder

    # Setup argument parser
    parser = argparse.ArgumentParser(description="Filter jsons by url.")
    parser.add_argument(
        "--input", required=True, help="The name of the folder with the jsons."
    )
    parser.add_argument("--output", required=True, help="Folder to write the jsons to.")

    # Parse arguments
    args = parser.parse_args()

    # get the file paths in the folder
    folder_path = args.input
    shard_paths = [
        os.path.join(folder_path, _)
        for _ in os.listdir(folder_path)
        if _.endswith(".zst")
    ]

    # shard_paths = shard_paths[:1]
    print(f"Total number of shards: {len(shard_paths)}")

    # Process shards in parallel
    ray.init()
    start_time = time.time()  # Start timing
    results = ray.get([process_shard.remote(path) for path in shard_paths])
    end_time = time.time()  # End timing
    print(f"Execution time: {end_time - start_time} seconds")  # Print the timing

    # Aggregate results
    total_tld_count = {tld: 0 for tld in tld_sites}
    for result in results:
        for tld, count in result.items():
            total_tld_count[tld] += count

    # Sort the TLD counts by count (descending) and then by TLD (ascending)
    sorted_tld_counts = sorted(
        total_tld_count.items(), key=lambda item: (-item[1], item[0])
    )

    # Pretty print the sorted results
    print("\nTLD Counts:")
    pprint(sorted_tld_counts)

    # Optionally, save the results to a file
    # output_file = "datasets/webinstruct/tld_counts.json"
    # os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # with open(output_file, "w") as f:
    #    json.dump(dict(sorted_tld_counts), f, indent=2)
    # print(f"\nResults saved to {output_file}")
