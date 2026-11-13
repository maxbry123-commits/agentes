# what about DeepMath~
datasets = """a1_math_deepmath
a1_math_automathtext
a1_math_open2math
a1_math_metamath
a1_math_formulas
a1_math_tiger_lab_math
a1_math_allenai_math
a1_math_tiger_math
a1_math_math_instruct
a1_math_college_math
a1_math_deepmind
a1_math_natural_reasoning
a1_math_openmathinstruct2
a1_math_hendrycks
a1_math_big_math
a1_math_numina_math
a1_math_gair_math
a1_math_baai_infinity_math
a1_math_lap1official_math
a1_math_metamath_aime
a1_code_star_coder_instruct
a1_code_codefeedback
a1_code_dolphin
a1_code_magicoder
a1_code_magpie
a1_code_McEval-Instruct
a1_code_octopack_sft
a1_code_opencoder
a1_code_react
a1_code_code_golf
a1_code_share_gpt_code
a1_code_stackexchange
a1_code_stackexchange_codereview
a1_code_kodcode
a1_code_primeintellect_code_understanding
a1_code_coder_stat
a1_code_reflection
a1_code_opencodereasoning
a1_code_code_contests
a1_code_tiny_codes
a1_code_apps
a1_code_codeforces_python_submissions
a1_code_primeintellect_real_world_swe
a1_code_primeintellect_stack_exchange
a1_code_glaive
a1_code_sql_create_context
a1_code_rosetta
a1_science_camel_physics
a1_science_cqadupstack
a1_science_camel_chemistry
a1_science_stackexchange_biology
a1_science_fineweb
a1_science_arxiv_biology
a1_science_wikipedia_biology
a1_science_wikipedia_field_of_science
a1_science_camel_biology
a1_science_pubmed_science
a1_science_stackexchange_physics
a1_science_biology_standardized
a1_science_organic_chem_pdfs"""

datasets = datasets.split("\n")
print(f"DATASETS: {datasets}")

yaml = """operators:"""

template = """
- id: load_{dataset}
  config:
    type: hf_source
    dataset: mlfoundations-dev/{dataset}
    split: train
- id: select_{dataset}
  config:
    type: function
    function: data_strategies.commons.select_columns
    function_config:
      columns: ["instruction_seed", "reasoning", "deepseek_solution","source", "conversations"]
  input_ids:
  - load_{dataset}
"""

for dataset in datasets:
    yaml += template.format(dataset=dataset)

yaml += """
- id: mix
  config:
    type: mix
    seed: 42
    add_shard_id_column: true
  input_ids:
"""
for dataset in datasets:
    yaml += f"  - select_{dataset}\n"

with open("./dcft/data_strategies/_Meta/meta_no_pipeline.yaml", "w") as f:
    f.write(yaml)
