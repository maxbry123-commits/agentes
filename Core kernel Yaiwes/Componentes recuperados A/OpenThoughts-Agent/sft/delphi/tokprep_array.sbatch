#!/bin/bash
#SBATCH --job-name=delphi-tokprep
#SBATCH --account=AIFAC_5C0_290
#SBATCH --partition=boost_usr_prod
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --array=0-26%9
#SBATCH --output=/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-prepared-tok/tokprep_%a.out

source /leonardo_work/AIFAC_5C0_290/bfeuer00/miniforge3/etc/profile.d/conda.sh
conda activate otagent
cd /leonardo_work/AIFAC_5C0_290/bfeuer00/code/OpenThoughts-Agent
source hpc/dotenv/leonardo.env && source ~/secrets.env
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export OMP_NUM_THREADS=8

BASES=(
delphi-3e18-p33m67-k0p20-lr83-a003 delphi-3e18-p50m50-k0p20-lr83-a003 delphi-3e18-p67m33-k0p20-lr83-a003
delphi-9e18-p33m67-k0p20-lr83-a002 delphi-9e18-p50m50-k0p20-lr83-a002 delphi-9e18-p67m33-k0p20-lr83-a002
delphi-2e19-p33m67-k0p20-lr83-a002 delphi-2e19-p50m50-k0p20-lr83-a002 delphi-2e19-p67m33-k0p20-lr83-a002
delphi-3e19-p33m67-k0p20-lr83-a002 delphi-3e19-p50m50-k0p20-lr83-a002 delphi-3e19-p67m33-k0p20-lr83-a002
delphi-9e19-p33m67-k0p20-lr83-a002 delphi-9e19-p50m50-k0p20-lr83-a002 delphi-9e19-p67m33-k0p20-lr83-a002
delphi-2e20-p33m67-k0p20-lr83-a001 delphi-2e20-p50m50-k0p20-lr83-a001 delphi-2e20-p67m33-k0p20-lr83-a001
delphi-3e20-p33m67-k0p20-lr83-a001 delphi-3e20-p50m50-k0p20-lr83-a001 delphi-3e20-p67m33-k0p20-lr83-a001
delphi-1e21-p33m67-9p25b-lr0.67-9cf8da delphi-1e21-p50m50-9p25b-lr0.83-f9edd2 delphi-1e21-p67m33-9p25b-lr0.67-ecbd27
delphi-1e22-p33m67-32p07b-lr0.67-54770ae7 delphi-1e22-p50m50-32p07b-lr0.5-ecfa99 delphi-1e22-p67m33-32p07b-lr0.33-4e8cc7a7
)
B=${BASES[$SLURM_ARRAY_TASK_ID]}
OUT=/leonardo_work/AIFAC_5C0_290/bfeuer00/experiments/delphi-prepared-tok/$B-prepared-tok
echo "TASK $SLURM_ARRAY_TASK_ID base=$B -> $OUT  $(date)"
if [ -f "$OUT/model.safetensors" ] || [ -f "$OUT/model.safetensors.index.json" ]; then
  echo "ALREADY-PREPARED $B"; exit 0
fi
python sft/delphi/prepare_delphi_tokenizer.py --model "laion/$B" --output "$OUT"
rc=$?
echo "RC=$rc base=$B"
if [ $rc -eq 0 ]; then
  python -c "
from transformers import AutoTokenizer
t=AutoTokenizer.from_pretrained(\"$OUT\")
for s in [\"<|start_think|>\",\"<|end_think|>\"]:
    ids=t.encode(s, add_special_tokens=False)
    print(\"CHECK\", s, ids, \"single\" if len(ids)==1 else \"FRAGMENTED\")
print(\"VOCAB\", len(t))
"
fi
echo "DONE base=$B rc=$rc $(date)"
exit $rc
