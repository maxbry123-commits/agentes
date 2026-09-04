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

# Create figure with two y-axes
fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()

# Plot stacked bars on primary y-axis
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

# Plot percentage line on secondary y-axis
ax2.plot(
    results["difficulty"],
    results["correct", "mean"] * 100,
    color="red",
    marker="o",
    linewidth=2,
    label="% Correct",
)

# Customize axes
ax1.set_xlabel("Difficulty Level")
ax1.set_ylabel("Number of Questions")
ax2.set_ylabel("Percentage Correct (%)")
plt.title("Questions by Difficulty Level with Accuracy Percentage")

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

plt.grid(True, alpha=0.3)
plt.show()
