# How to generate datasets?

Dataset generation pipelines are defined by all `.yaml` files in the `dcft/data_strategies` folder structure (any depth of subfolder). 
These `.yaml` files are all uniquely named and the name of the file is the name of that data framework and the name of the dataset that gets uploaded to huggingface. 

To see all the available data generation pipelines run 

```bash
python -m dcft.generate --list --dev
```

Running an framework is done with the following command. Note `--dev` runs a local ray cluster and writes the intermediates datasets to the `/datasets` folder and the curator cache is by default `~/.cache/curator`. Datasets created with `--dev` are not added to the database. This is useful for rapidly debugging your pipeline during development. Use `--remote` when you want to generate a dataset that is officially recorded in the datasets database. This will send the job to the remote ray cluster and will write intermediate datasets and the curator cache to google cloud storage, updating the database as well. 

```bash
    python -m dcft.generate  --framework <name of framework> --remote
```

When running a job remotely:

1. The job is submitted to a Ray cluster specified by the `ray_address` in the `SyntheticDataFramework` class.
2. The entire working directory is packaged and sent to the remote cluster, excluding large files and directories specified in the `excludes` list.
3. The `HF_TOKEN` and `OPENAI_API_KEY` environment variables are automatically set in the remote environment based on the values in the local environment. If you want to set other environment variables, you can do so by adding them to the `env_vars` dictionary of the job being submitted by the `run_remote` method in the `SyntheticDataFramework` class.
4. You can monitor the job's progress using the provided Ray dashboard URL.
5. The script will wait for the job to complete and provide status updates.

Note: Make sure you have the necessary environment variables (HF_TOKEN, OPENAI_API_KEY) set before running a remote job.

## Viewing Datasets
You can view the intermediate datasets in a pipeline with `dcft.view`, this works with both `--remote` and `--dev`. 

```bash
    python -m dcft.view  --framework <name of framework> --remote
```

## Tutorial: How to add support for new datasets

1. Create a new folder for yaml files in `dcft/data_strategies`. Please organize this into a reasonable place based on existing folder structure. 
2. Create a yaml file with your dataset generation details

3. Run the command above with your new task name. 

## Designing each step of your dataset generation pipeline

There are two rules for your operators: they must return a HuggingFace dataset and you must specify the typing for dataset inputs in the function signature. There are a few types of Operators: 

1. hf_source - prebuilt to load in a dataset from HuggingFace
2. function - custom functionality specified in a python file

Each step in your data generation pipeline is an Operator that either takes in nothing and returns a dataset or takes in one or more datasets and returns a dataset. You need only specify the name of the dataset and the individual operators which constitute the data generation process. The data generation process is modeled as a Directed Acyclic Graph, which should be general enough to handle many different workloads. 

A DAG configuration typically contains the following elements:

1. name: A unique identifier for the DAG.
2. operators: A list of operators that define the processing steps.
3. output_ids: (Optional) A list of operator IDs whose outputs should be considered as the final output of the DAG. (mostly unused by our frameworks)

Each operator in the DAG is defined with the following properties:

1. id: A unique identifier for the operator within the DAG.
2. config: The configuration specific to the operator type.
3. input_ids: (Optional) A list of operator IDs that provide input to this operator.


To specify the inputs to each operator, you use "input_ids". If not specified in the yaml, it is assumed that this operator needs no input. Otherwise, you must specify it. If you need outputs from multiple previous operators, please add them in a list i.e. "input_ids: [evol_instruction, rename_prompt]." If your function requires multiple datasets as input, but only one dataset is seen in the respective function signature, the datasets from the parent nodes will be concatenated. However, if there are multiple datasets in the function signature, you can either

1. Specify input_dataset_map in your config which maps the argument name in your function to the input_id.
2. Leave input_dataset_map blank which will trigger default behavior where the order of your input_ids will be passed in the order of the datasets in the function signature. 

## Special Case: you need inputs from several operators but they can't be concatenated

There are two cases.

1. You specify two input_ids, but your function has only one dataset in the arguments.  

```yaml
  - id: dedup_evol_instructions
    config:
      type: function
      function: data_strategies.EvolInstruct.utils.dedup
      function_config:
        input_column: evol_instruction
    input_ids:
      - instruction_generation
      - load_alpaca
```

```python
def dedup(dataset: Dataset, input_column: str) -> Dataset:
    """
    Remove duplicate rows from the dataset based on a specific column.

    Args:
        dataset (Dataset): The input dataset.
        input_column (str): The name of the column to check for duplicates.

    Returns:
        Dataset: The dataset with duplicate rows removed.
    """
    # Convert to pandas DataFrame
    df = dataset.to_pandas()

    # Drop duplicate rows based on the specified column
    df_cleaned = df.drop_duplicates(subset=[input_column], keep="first")

    # Convert back to Hugging Face Dataset
    cleaned_dataset = Dataset.from_pandas(df_cleaned)

    return cleaned_dataset
```

Here, the inputs from load_alpaca and instruction_generation will be concatenated into a single dataset and passed to your function (in a sharded manner if you specify it).

2. You specify two input_ids, but your function has two datasets in the arguments. 

You can specify input_dataset_map:
```yaml
  - id: dedup_evol_instructions
    config:
      type: function
      function: data_strategies.EvolInstruct.utils.dedup
      input_dataset_map:
        dataset: load_alpaca
        dataset2: instruction_generation
      function_config:
        input_column: evol_instruction
    input_ids:
      - instruction_generation
      - load_alpaca
```

```python
def dedup(input_column: str, dataset: Dataset, dataset2: Dataset) -> Dataset:
    """
    Remove duplicate rows from the dataset based on a specific column.

    Args:
        dataset (Dataset): The input dataset.
        input_column (str): The name of the column to check for duplicates.

    Returns:
        Dataset: The dataset with duplicate rows removed.
    """
    print(f"dataset 1 columns {dataset.column_names}")
    print(f"dataset 2 columns {dataset2.column_names}")

    # Convert to pandas DataFrame
    df = dataset.to_pandas()

    # Drop duplicate rows based on the specified column
    
    df_cleaned = df.drop_duplicates(subset=[input_column], keep="first")

    # Convert back to Hugging Face Dataset
    cleaned_dataset = Dataset.from_pandas(df_cleaned)

    return cleaned_dataset
```
Here, dataset will correspond with the dataset from load_alpaca and dataset2 will be the dataset associated with instruction_generation.


IMPORTANT: Such functions cannot be done in a sharded fashion. We do not want to assume how different shards from the inputs will be merged and paired, so we leave that behaviour to be chosen by the user. 

## Specifying the output of your pipeline
To specify the final output of your entire dataset generation process, please specify "output_ids" as a list of id's from which the output will be stored on HuggingFace. If multiple datasets are in output_ids, they will be concatenated together. If output_ids is left empty, the outputs from the final leaf operator in your DAG after topological sort will be treated as the output_ids (if there are multiple leaf nodes), we highly encourage specifying output_ids. 


## Helpful Tips
1. If an individual function can operate on only a smaller shard of the dataset, please specify "sharded=True". An example of a function that may need the entire dataset is a deduplication operator.
2. We provide an HFSourceOperator that has custom code to load a HF dataset. 
3. We highly encourage specifying output_ids of your data generation process unless you know what you are doing.
4. We highly encourage specifying input_ids of each operatore unless you know what you are doing. 

## Dataset Mixing
Say you want to create a mix of multiple datasets. You need only create a YAML file that loads these datasets from preexisting frameworks or generate these datasets with a new pipeline. 

```yaml
operators:
- id: mix_banana
  input_ids: ['load_evol_instruct', 'shp_dag']
  config:
    type: mix
- id: load_evol_instruct
  input_ids: []
  config:
    type: load_preexisting
    framework_name: evol_instruct
- id: shp_dag
  input_ids: []
  config:
    type: dag
    dag:
      name: shp_processing
      operators:
        - id: load_shp
          config:
            type: hf_source
            dataset: stanfordnlp/SHP
            split: train
            columns: 
              - history
              - human_ref_A
            num_truncate: 3

        - id: instruction_generation
          config:
            type: function
            sharded: true
            function: data_strategies.EvolInstruct.utils.instruction_generation
            function_config:
              input_column: history
              output_column: evol_instruction
        
        - id: dedup_evol_instructions
          config:
            type: function
            function: data_strategies.EvolInstruct.utils.dedup
            function_config:
              input_column: evol_instruction

        - id: annotate
          config:
            type: function
            sharded: true
            function: data_strategies.EvolInstruct.utils.annotate
            function_config:
              input_column: evol_instruction
              output_column: completion

        - id: rename_prompt
          config:
            type: function
            sharded: true
            function: data_strategies.EvolInstruct.utils.force_rename_column
            function_config:
              old_name: evol_instruction
              new_name: prompt

        - id: remove_other_columns
          config:
            type: function
            sharded: true
            function: data_strategies.EvolInstruct.utils.remove_other_columns
            function_config:
              columns_to_keep:
                - prompt
                - completion
```

In the above example, we are mixing two datasets: 

* The first dataset is evol_instruct, which is loaded from `dcft/data_strategies/WizardLM/wizard_lm.yaml`,
* The second dataset is shp_processing, which is defined as a DAG, see the [Nested DAGs](#nested-dags) section for more details.
* These two datasets are mixed together with the `mix_banana` operator to form the final dataset.

## Debugging Ray Code

Debugging your code can be tricky due to the use of Ray. We recommend the following steps. 
1. Place a breakpoint() in your code
2. Wait till breakpoint is encountered (this will be logged)
3. In a seperate terminal, run "ray debug"
4. Specify which thread you want to debug (0 is a good choice for most cases)
5. This will work like normal PDB
