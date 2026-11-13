# Hierarchical Research Agent System (HiRAS)

Hierarchical Research Agent System (HiRAS)

This repository contains the implementation of the Hierarchical Research Agent System (HiRAS), a multi-agent framework for automated research paper replication.

## Preparation

### Data Preparation
1. Please download the paper data from [PaperBench](https://github.com/openai/frontier-evals/tree/main/project/paperbench) and [Paper2Code] (https://github.com/going-doer/Paper2Code)
2. Put the benchmarks under the ```data/``` directory, following the structure:
```
data/
├── paperbench/
│   ├── adaptive-pruning/
│   │   ├── paper.md
│   │   ├── addendum.md
│   │   └── ...
│   ├── all-in-one/
│   │   └── ...
│   └── ...
└── paper2code/
    ├── dataset_info.json
    ├── iclr2024/
    │   ├── auto-j_cleaned.json
    │   └── ...
    ├── icml2024/
    └── nips2024/

``` 

### Model Preparation
Specify the model API base URL and authentication credentials in ```run.py```.

### Environment Preparation
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```
2. Create a base environment for running experiments to avoid interference with the system environment. For example:
```bash
conda create -n ExpBase python=3.11
conda activate ExpBase

pip install -r exp_env_example.txt

conda deactivate
```

3. Following the configuration in ```run.sh```, specify:
- the base environment (ExpBase)
- a temporary execution environment name that will be copied from the base environment for running experiments.

This setup ensures isolation across runs.

## Experiments Execution
Please refer to ```run.sh``` for example commands to execute the HiRAS framework. By default, all experimental outputs will be saved to the ```output/``` directory.