# Run DCFT experiments on a supercomputer

## Quick Start

### Main command
```
python3 -m hpc.launch --train_config_path your.yaml --time_limit 24:00:00 --num_nodes 1 --dataset your/dataset [additional arguments for HPC / LLamaFactory]
```

For the yaml, the ones for the paper are 
- dcft/train/hp_settings/paper/reasoning_small.yaml 
- dcft/train/hp_settings/paper/reasoning_medium.yaml 
- dcft/train/hp_settings/paper/reasoning_large.yaml 

> [!TIP]  
> Add `--dry_run` to see the outputs (sbatch, yaml, etc.) wihtout launching the job


## Examples Launching

> [!CAUTION]  
> If you are not running a pipeline experiment, check to see if it should use `small` or `large` hyperparameters

Before you run this, make sure you run setups that is relevant to your cluster below

#### Example pipeline
```
cd $DCFT_PRIVATE
$DCFT_PRIVATE_ACTIVATE_ENV
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/paper/reasoning_medium.yaml --time_limit 24:00:00 --num_nodes 16 --dataset mlfoundations-dev/a1_math_formulas
```

#### Multinode (3) test on a dataset with 192 rows and HP with 96 GBS and 1 epoch
```
cd $DCFT_PRIVATE
$DCFT_PRIVATE_ACTIVATE_ENV
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/reasoning_test.yaml --time_limit 01:00:00 --num_nodes 3 --dataset mlfoundations-dev/s1k-1.1-test-192
```

#### Example 32B

> [!CAUTION]  
> Check in the sheet see if you should use `small`, `medium` or `large` hyperparameters

Tip: you might want to use more nodes

```
cd $DCFT_PRIVATE
$DCFT_PRIVATE_ACTIVATE_ENV
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/<CHECK_HP_SETTING> --time_limit 24:00:00 --num_nodes 16 --dataset <HF_ORG/HF_REPO> --model_name_or_path Qwen/Qwen2.5-32B-Instruct 
```


#### Examples Setups (Add these to your ~/.bashrc)

Add these to your ~/.bashrc (HF necessary, WANDB optional)
```
export HF_TOKEN=<ENTER_YOUR_HF_TOKEN>
export WANDB_TOKEN=<ENTER_YOUR_WANDB_TOKEN>

# Only run this part once, no need to add to your ~/.bashrc
# huggingface-cli login --token $HF_TOKEN
# wandb login $WANDB_TOKEN
```

Then based on your cluster:
(added the [symlink)](https://docs.marlowe.stanford.edu/ngc_example.html)

#### TACC
```
source /scratch/08002/gsmyrnis/dcft_shared/dcft_private/hpc/dotenv/tacc.env
source $DCFT_PRIVATE/hpc/scripts/common.sh
rm -rf ~/.cache/huggingface/
ln -s $HF_HUB_CACHE ~/.cache/huggingface
```

#### ZIH
```
export DCFT=/data/cat/ws/ryma833h-dcft
source $DCFT/dcft_private/hpc/dotenv/zih.env
source $DCFT_PRIVATE/hpc/scripts/common.sh

# Run this part once, instead of putting ~/.bashrc
rm -rf ~/.cache/huggingface/
ln -s $HF_HUB_CACHE ~/.cache/huggingface
```

#### LEONARDO
```
source /leonardo_work/EUHPC_E03_068/DCFT_shared/dcft_private/hpc/dotenv/leonardo.env
source $DCFT_PRIVATE/hpc/scripts/common.sh
```

#### JEDI
```
source /p/project1/laionize/dcft/dcft_private/hpc/dotenv/jupiter.env
source $DCFT_PRIVATE/hpc/scripts/common.sh
```

#### JURECA
```
source /p/project1/laionize/dcft/dcft_private/hpc/dotenv/jureca.env
source $DCFT_PRIVATE/hpc/scripts/common.sh
```

## Monitoring your job

The submission script prints out the job id and log file path. 

SLURM logs are determined by the following `#SBATCH --output={experiments_dir}/logs/%x_%j.out`. 
```
tail $DCFT/experiments/logs/<job_name>_<job_id>.out`
```

The output files from llamafactory are written to `$CHECKPOINTS_DIR`. The `trainer_log.jsonl` will say what the estimated finish time is. 
```
tail $CHECKPOINTS_DIR/<job_name>/trainer_log.jsonl`
```

You can monitor if your job is running with `squeue -u $USER` or the [alias](https://github.com/mlfoundations/dcft_private/tree/main/hpc#helpful-aliases) `sqme` which formats so you can see the full job name. Look to the next section for more aliases which help monitor your jobs. 

## Helpful Aliases

Check out [`hpc/scripts/common.sh`](scripts/common.sh) to see all the definitions or do `which <alias>`

### Job Monitoring
- `sqme` shows all your queued jobs with formatted output
- `sqteam` shows all the queued jobs that are using the same slurm account as you
- `sqthem <user>` shows all queued jobs for a specific user
- `sfail [<hours>]` shows all the jobs that failed in the last N (default 1) hours
- `swin [<hours>]` shows all the jobs that completed successfully in the last N (default 1) hours
- `soops [<hours>]` shows all the jobs that were cancelled in the last N (default 1) hours
- `status [<lines>]` shows checkpoint logs (always 1 line) and tails SLURM logs (specified number of lines, default: 1)
- `sinf` shows formatted cluster information

You can pipe any job listing command to `status` to see detailed information about those jobs (e.g., `sfail | status` to check recently failed jobs). You can also filter jobs using grep before passing to status, like `sqme | grep a1_math_numina | status 50` to see the last 50 log lines for jobs matching "a1_math_numina"

### Job Launching
- `goeval <experiment-name>` eval mlfoundations-dev model on pipeline evals (`a1_math_deepmath`)
- `sloweval <experiment-name>` eval model with less shards (4 instead of 16) 
- `fulleval <experiment-name>` eval model on full reasoning evals including held out (`fig1_scaling_openthoughts_10k`)
- `gotrain <experiment-name>` train standard (***medium***) hp on mlfoundations-dev model (`fig1_scaling_openthoughts_10k`)
- `gosmall <experiment-name>` train **small** hp on mlfoundations-dev model (`fig1_scaling_openthoughts_1k`)
- `golarge <experiment-name>` train **large** hp on mlfoundations-dev model (`fig1_scaling_openthoughts_100k`)
- `gofast <experiment-name>` train with more GPUs for faster training

### Cleanup
- `rmlogs [<job-id>]` removes log files with numbers below the specified threshold. If no threshold is provided, you will be prompted to enter one.

## Launching a bunch of things at the same time

Make sure you have sourced the /hpc/dotenv.

Then you can do the following, by copy and pasting from the [experiment sheet](https://docs.google.com/spreadsheets/d/11ThWrGsEpT56Hxa_C3JyVEP33lt2V2fz1XSu0kcXdo8/edit?gid=1579018090#gid=1579018090) a bunch of cells
Into the following and running it (change `goeval` to `fulleval` or `gotrain`, `gosmall`, `golarge`)
```
cat << 'EOF' | while read -r model; do [[ -z "$model" ]] || fulleval "$model"; done
Qwen/Qwen2.5-7B-Instruct
open-r1/OpenR1-Qwen-7B
open-r1/OlympicCoder-7B
open-thoughts/OpenThinker-7B
open-thoughts/OpenThinker2-7B
bespokelabs/Bespoke-Stratos-7B
deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
GAIR/LIMR
PRIME-RL/Eurus-2-7B-SFT
PrimeIntellect/SYNTHETIC-1-SFT-7B
EOF
```

If you mess up, cancel jobs
```
scancel -u $USER -t PENDING
```

## More docs
FYI everything else below might be out of date  
- [TACC](docs/TACC.md)
- [ZIH](docs/ZIH.md)
- [leonardo](docs/leonardo.md)
- [hpc_launcher](docs/hpc_launcher.md)
