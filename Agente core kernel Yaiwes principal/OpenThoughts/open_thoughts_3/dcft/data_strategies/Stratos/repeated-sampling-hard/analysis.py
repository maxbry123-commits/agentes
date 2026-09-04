import matplotlib.pyplot as plt
import pandas as pd
from datasets import load_dataset

dataset = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty",
    split="train",
)

# Convert to pandas DataFrame for easier analysis
df = pd.DataFrame(dataset)

# Calculate percentages and counts for each difficulty level
results = (
    df.groupby("difficulty").agg({"correct": ["mean", "count", "sum"]}).reset_index()
)

# Calculate incorrect counts
results["correct", "incorrect"] = (
    results["correct", "count"] - results["correct", "sum"]
)

# Print percentages
for _, row in results.iterrows():
    difficulty = int(row["difficulty"])
    correct_pct = row[("correct", "mean")] * 100
    print(f"Difficulty {difficulty:.0f}: {correct_pct:.1f}% correct")

for _, row in results.iterrows():
    difficulty = int(row["difficulty"])
    incorrect_count = row[("correct", "incorrect")]
    print(f"Difficulty {difficulty:.0f}: {incorrect_count:.0f} incorrect")

# Create figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Plot stacked bars on first subplot
correct_bars = ax1.bar(
    results["difficulty"], results["correct", "sum"], label="Correct"
)
incorrect_bars = ax1.bar(
    results["difficulty"],
    results["correct", "incorrect"],
    bottom=results["correct", "sum"],
    label="Incorrect",
)

# Add count labels to the bars
for bars in [correct_bars, incorrect_bars]:
    for bar in bars:
        height = bar.get_height()
        y_pos = bar.get_y() + height / 2
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            y_pos,
            f"{int(height)}",
            ha="center",
            va="center",
        )

# Customize first subplot
ax1.set_xlabel("Difficulty Level")
ax1.set_ylabel("Number of Questions")
ax1.set_title("Questions by Difficulty Level")
ax1.legend(loc="upper right")
ax1.grid(True, alpha=0.3)

# Plot percentage line on second subplot
ax2.plot(
    results["difficulty"],
    results["correct", "mean"] * 100,
    color="red",
    marker="o",
    linewidth=2,
)

# Customize second subplot
ax2.set_xlabel("Difficulty Level")
ax2.set_ylabel("Percentage Correct (%)")
ax2.set_title("Accuracy Percentage by Difficulty")
ax2.grid(True, alpha=0.3)

# Adjust layout to prevent overlap
plt.tight_layout()
plt.show()
