#!/bin/bash
#SBATCH -p mcml-hgx-h100-92x4
#SBATCH -q mcml
#SBATCH --nodes {num_nodes}
#SBATCH --ntasks 1
#SBATCH --gres=gpu:{gpus_per_node}
#SBATCH --time={time_limit}
#SBATCH --job-name={job_name}
#SBATCH --output={experiments_dir}/logs/%x_%j.out

# set environment variables
export PATH=/usr/local/cuda/bin:/dss/dsshome1/09/ge52het2/miniconda3/condabin:/dss/dsshome1/09/ge52het2/miniconda3/envs/dcfttrain/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/opt/conda/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONPATH=$HOME/dcft_private:$PYTHONPATH
export CUDA_HOME=/usr/local/cuda-12
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export FI_EFA_FORK_SAFE=1
export FI_LOG_LEVEL=1
export FI_EFA_USE_DEVICE_RDMA=1
export NCCL_NET_GDR_LEVEL="SYS"
export NCCL_NET_GDR_READ=1
export PYTHONFAULTHANDLER=1
export CUDA_LAUNCH_BLOCKING=0
export OMPI_MCA_mtl_base_verbose=1
export FI_EFA_ENABLE_SHM_TRANSFER=0
export FI_PROVIDER=efa
export FI_EFA_TX_MIN_CREDITS=64
export NCCL_TREE_THRESHOLD=0
export NCCL_DEBUG=INFO
export FORCE_TORCHRUN=1

export OUTLINES_CACHE_DIR="/tmp/.outlines"
export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=12802

export CONDA_PREFIX=/dss/dsshome1/09/ge52het2/miniconda3/envs/dcfttrain
export HF_HOME="/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/reinhard/hub"
export TRITON_CACHE_DIR="/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/reinhard/triton_cache"

export $(grep -v '^#' "$HOME/dcft_private/.env" | xargs)
export CONFIG_FILE="$HOME/dcft_private/dcft/train/configs/mammoth/llama3_mammoth_dcft_ablation.yaml"

srun --export=ALL,HOME="/dss/dsshome1/09/ge52het2" \
     --container-image="/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/anselm/rh_img_devel.sqsh" \
     --container-mounts="$HOME:$HOME,/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/reinhard:/dss/dssmcmlfs01/pn57vo/pn57vo-dss-0000/reinhard" \
     bash -c "
    # Load Conda and activate environment
    echo "adfadf"
    echo $HOME
    source $HOME/miniconda3/etc/profile.d/conda.sh
    conda activate dcfttrain  # install with dcft/train/requirements.txt

    cd $HOME/dcft_private
    huggingface-cli login --token $HF_TOKEN

    # run the training script
    torchrun --standalone --nproc-per-node 4 $HOME/dcft_private/dcft/train/llamafactory/src/train.py $CONFIG_FILE
    "