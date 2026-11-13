#!/bin/bash
# keeper-26 TACC refill runner — 3 front-door listeners, ~42s stagger, rows 271-274
set -u
REPO=/scratch/10635/penfever/OpenThoughts-Agent
PY=/scratch/10635/penfever/miniconda3/envs/otagent/bin/python
LOGDIR=/scratch/10635/penfever/keeper26_logs
mkdir -p "$LOGDIR"

launch() {
  local sess=$1 preset=$2 list=$3
  tmux kill-session -t "$sess" 2>/dev/null
  tmux new-session -d -s "$sess" "cd $REPO && source /scratch/10635/penfever/keys.env && source hpc/dotenv/tacc.env && $PY -m hpc.launch --job_type eval_listener --cluster-config tacc --require-priority-list --priority-file eval/lists/$list --config-yaml dcagent_eval_config_no_override.yaml --force-reeval --preset $preset --once --verbose 2>&1 | tee $LOGDIR/$sess.log"
  echo "launched $sess (preset=$preset list=$list)"
}

launch keeper26_v2  v2       tacc_keeper26_v2_0703.txt
sleep 42
launch keeper26_swe swebench tacc_keeper26_swe_0703.txt
sleep 42
launch keeper26_tb2 tb2      tacc_keeper26_tb2_0703.txt
echo "all 3 listeners launched; logs in $LOGDIR"
