import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from datasets import concatenate_datasets, load_dataset

# There are three datasets with labeled numina difficulty:
# https://huggingface.co/datasets/NovaSky-AI/labeled_numina_difficulty
# https://huggingface.co/datasets/NovaSky-AI/labeled_numina_difficulty_859K
# https://huggingface.co/datasets/NovaSky-AI/labeled_numina_difficulty_162K

# Load all three datasets
datasets = {
    "labeled_numina_difficulty": load_dataset(
        "NovaSky-AI/labeled_numina_difficulty", split="train"
    ),
    "labeled_numina_difficulty_859K": load_dataset(
        "NovaSky-AI/labeled_numina_difficulty_859K", split="train"
    ),
    "labeled_numina_difficulty_162K": load_dataset(
        "NovaSky-AI/labeled_numina_difficulty_162K", split="train"
    ),
}

# Create a dictionary to store difficulty distributions
difficulty_counts = {}

#### SECTION 1:
# Calculate difficulty distributions for each dataset
# easy = datasets['labeled_numina_difficulty_162K'].filter(lambda x: x['gpt_difficulty_parsed'] <= 3)
# medium_hard = datasets['labeled_numina_difficulty_859K'].filter(lambda x: x['gpt_difficulty_parsed'] >= 4)
# mix = concatenate_datasets([easy, medium_hard])
# print(mix) # 459,287

# # print(mix.unique('source')) # ['amc_aime', 'math', 'olympiads', 'cn_k12', 'synthetic_math', 'orca_math', 'synthetic_amc', 'aops_forum', 'gsm8k']

# smaller_mix = mix.filter(lambda x: x['source'] in ['amc_aime', 'olympiads', 'aops_forum', 'math'])
# print(smaller_mix) # 195,618

# selections = datasets['labeled_numina_difficulty_859K'].filter(lambda x: x['source'] in ['amc_aime', 'olympiads', 'aops_forum', 'math'])
# print(selections) # 192,322
# ok so these aren't disjoint, this makes me think the the LLM judge of difficulty is not good.


#### SECTION 2:
# # Calculate difficulty distributions for each dataset
# for name, dataset in datasets.items():
#     difficulties = dataset['gpt_difficulty_parsed']
#     print(f"\n{name} difficulty range: {min(difficulties)} - {max(difficulties)}")

#     # Count occurrences of each difficulty level
#     counts = pd.Series(difficulties).value_counts().sort_index()
#     difficulty_counts[name] = counts

# # Create DataFrame with counts
# df = pd.DataFrame(difficulty_counts).fillna(0)
# df.index = df.index.astype(int)  # Ensure indices are integers
# df = df.sort_index()

# # Save to CSV
# df.to_csv('difficulty_distributions.csv')

# # Create visualization
# plt.figure(figsize=(12, 6))
# for name in datasets.keys():
#     plt.plot(df.index, df[name], marker='o', label=name)

# plt.title('Difficulty Distribution Across Datasets')
# plt.xlabel('Difficulty Level')
# plt.ylabel('Count')
# plt.legend()
# plt.grid(True)
# plt.savefig('difficulty_distributions.png')
# plt.show()

# # Print the distribution table
# print("\nDifficulty Distribution Table:")
# print(df)


#### SECTION 3:
# Create a combined dataset from 162K (levels 1-3) and 859K (levels 4+)
# df_162k = pd.DataFrame({'difficulty': datasets['labeled_numina_difficulty_162K']['gpt_difficulty_parsed']})
# df_859k = pd.DataFrame({'difficulty': datasets['labeled_numina_difficulty_859K']['gpt_difficulty_parsed']})

# # Filter datasets based on difficulty levels
# low_difficulty = df_162k[df_162k['difficulty'] <= 3]
# high_difficulty = df_859k[df_859k['difficulty'] >= 4]

# # Combine the filtered datasets
# combined_distribution = pd.concat([low_difficulty, high_difficulty])

# # Calculate and display the distribution of the combined dataset
# combined_counts = combined_distribution['difficulty'].value_counts().sort_index()
# print("\nCombined Dataset Distribution:")
# print(combined_counts)

# # Add the combined distribution to the main DataFrame
# df['combined_dataset'] = combined_counts

# # Update the visualization with the new combined dataset
# plt.figure(figsize=(12, 6))
# for column in df.columns:
#     plt.plot(df.index, df[column], marker='o', label=column)

# plt.title('Difficulty Distribution Across Datasets (Including Combined)')
# plt.xlabel('Difficulty Level')
# plt.ylabel('Count')
# plt.legend()
# plt.grid(True)
# plt.savefig('difficulty_distributions_with_combined.png')
# plt.show()

#### SECTION 4:
# Calculate difficulty distributions for each dataset
full_numina = datasets["labeled_numina_difficulty_859K"]
difficulties = full_numina["gpt_difficulty_parsed"]
print(f"\nfull_numina difficulty range: {min(difficulties)} - {max(difficulties)}")

difficulty_counts = {}

for source in full_numina.unique("source"):
    subset = full_numina.filter(lambda x: x["source"] == source)
    difficulties = subset["gpt_difficulty_parsed"]
    print(f"\n{source} difficulty range: {min(difficulties)} - {max(difficulties)}")
    # Count occurrences of each difficulty level
    counts = pd.Series(difficulties).value_counts().sort_index()
    difficulty_counts[source] = counts

# Create DataFrame with counts
df = pd.DataFrame(difficulty_counts).fillna(0)
df.index = df.index.astype(int)  # Ensure indices are integers
df = df.sort_index()

# Save to CSV
df.to_csv("difficulty_distributions_by_source.csv")

# Create visualization
plt.figure(figsize=(12, 6))
# for source in full_numina.unique('source'):
for source in ["amc_aime", "olympiads", "aops_forum", "math"]:
    plt.plot(df.index, df[source], marker="o", label=source)

plt.title("Difficulty Distribution By Source in Numina 859K (Selected Sources)")
plt.xlabel("Difficulty Level")
plt.ylabel("Count")
plt.legend()
plt.grid(True)
plt.savefig("difficulty_distributions_by_source.png")
plt.show()

# Print the distribution table
print("\nDifficulty Distribution Table:")
print(df)
