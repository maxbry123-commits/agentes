from datasets import concatenate_datasets, load_dataset
from filtering import filter_problems

# construction
# numina_total:  859494
# selected_numina:  192302
# filtered_numina:  151522
# omni:  4428
# math_mix:  155950

numina = load_dataset("AI-MO/NuminaMath-CoT", split="train")
print("numina_total: ", len(numina))

selected_numina = numina.filter(
    lambda x: x["source"] in ["amc_aime", "olympiads", "aops_forum", "math"]
)
print("selected_numina: ", len(selected_numina))

filtered_numina = selected_numina.filter(filter_problems)
print("filtered_numina: ", len(filtered_numina))

filtered_numina.push_to_hub("mlfoundations-dev/math_stratos_scale_pre_decontamination")
