meta_no_pipeline = """
operators:
- id: load_hf
  config:
    type: hf_source
    dataset: mlfoundations-dev/meta_no_pipeline
    split: train
- id: sample_dataset
  config:
    type: function
    function: data_strategies.commons.uniform_sample_fixed
    function_config:
      num_samples: {num_samples}
  input_ids:
  - load_hf
"""

scales = {
    "1k": 1_000,
    "3k": 3_160,
    "10k": 10_000,
    "30k": 31_600,
    "100k": 100_000,
    "300k": 316_000,
    "1000k": 1_000_000,
}

for scale, num_samples in scales.items():
    with open(
        f"dcft/data_strategies/_FIG1_Comparison/fig1_scaling_no_pipeline_{scale}.yaml",
        "w",
    ) as f:
        f.write(meta_no_pipeline.format(num_samples=num_samples))
