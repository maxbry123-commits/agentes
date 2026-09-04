import pandas as pd
from datasets import load_dataset
from math_verify.metric import math_metric
from math_verify.parser import ExprExtractionConfig, LatexExtractionConfig

judge_result = load_dataset("mlfoundations-dev/math_stratos_scale_judged_and_annotated")

gold_is_latex = True
verify_func = math_metric(
    gold_extraction_target=(
        LatexExtractionConfig() if gold_is_latex else ExprExtractionConfig(),
    ),
    pred_extraction_target=(ExprExtractionConfig(), LatexExtractionConfig()),
    aggregation_function=max,
    fallback_mode="first_match",
    precision=6,
)


def validate_solution(row):
    """Validate a single solution using the verification function."""
    extracted_answers = ""  # Initialize as empty string instead of None
    gold_answers = ""  # Initialize as empty string instead of None
    grade = 0
    try:
        # Use the verification function
        grade, extracted_answers = verify_func(
            [row["ground_truth_solution"]], [row["deepseek_solution"]]
        )

        if extracted_answers is None:
            extracted_answers = ""  # Use empty string instead of None
            gold_answers = ""  # Use empty string instead of None
        else:
            gold_answers = str(extracted_answers[0])  # Convert to string
            extracted_answers = str(extracted_answers[1])  # Convert to string

        return {
            **row,  # Keep all existing fields
            "extracted_answer": extracted_answers,
            "extracted_gold": gold_answers,
            "verifier_label": grade == 1,
            "error": "",  # Empty string instead of None
        }

    except Exception as e:
        return {
            **row,  # Keep all existing fields
            "extracted_answer": extracted_answers,
            "extracted_gold": gold_answers,
            "verifier_label": grade == 1,
            "error": str(e),
        }


# Replace the for loop with this:
validated_results = judge_result.map(
    validate_solution,
    num_proc=16,
    desc="Validating solutions",  # Adjust based on your CPU cores
)


validated_results.push_to_hub("mlfoundations-dev/math_stratos_scale_verified_with_hf")

# ### VERIFIER MISMATCHES ###

# # Take first 1000 samples
# sample_data = validated_results.select(range(1000))

# # Find mismatches
# def find_mismatches(row):
#     is_mismatch = row['verifier_label'] != row['correct']  # 'is_correct' is the original label
#     if is_mismatch:
#         return {
#             'problem': row['problem'],
#             'deepseek_solution': row['deepseek_solution'],
#             'ground_truth_solution': row['ground_truth_solution'],
#             'verifier_label': row['verifier_label'],
#             'original_label': row['correct'],
#             'extracted_answer': row['extracted_answer'],
#             'extracted_gold': row['extracted_gold']
#         }
#     return None


# mismatches = [find_mismatches(row) for row in sample_data]
# mismatches = [m for m in mismatches if m is not None]

# # Print summary statistics
# print(f"Total mismatches in first 1000 samples: {len(mismatches)}")
# print(f"Mismatch rate: {len(mismatches)/1000:.2%}")

# # Print detailed analysis of first few mismatches
# print("\nDetailed analysis of first 10 mismatches:")
# for i, mismatch in enumerate(mismatches[:10]):
#     print(f"\nMismatch #{i+1}:")
#     print(f"Problem: {mismatch['problem']}")
#     print(f"DeepSeek solution: {mismatch['deepseek_solution']}")
#     print(f"Ground truth: {mismatch['ground_truth_solution']}")
#     print(f"Verify label: {mismatch['verifier_label']}")
#     print(f"Original label: {mismatch['original_label']}")
#     print(f"Extracted answer: {mismatch['extracted_answer']}")
#     print(f"Extracted gold: {mismatch['extracted_gold']}")
#     print("-" * 80)

# # Optionally, save mismatches to a CSV for further analysis
# mismatches_df = pd.DataFrame(mismatches)
# mismatches_df.to_csv('mismatches_analysis.csv', index=False)
