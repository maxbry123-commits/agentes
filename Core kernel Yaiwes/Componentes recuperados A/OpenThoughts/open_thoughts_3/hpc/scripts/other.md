# Generate scaling datasets
git switch main
cat << 'EOF' | while read -r model; do [[ -z "$model" ]] || python dcft/data_strategies/direct_scale_generator.py --hf "mlfoundations-dev/$model" --max-scale 10k; done
HERE
EOF

# Retroactively adding dependency post-hoc
evalchemy
sqteam | grep -v eval | awk 'NR>1 {job_id=$1; model_name=$3; print "python eval/distributed/launch_simple.py --tasks AIME24,AMC23,MATH500,MMLUPro,JEEBench,GPQADiamond,LiveCodeBench,CodeElo,CodeForces --num_shards 16 --max-job-duration 4 --dependency afterok:" job_id " --model_name mlfoundations-dev/" model_name}' | bash

# Launching multiple scales (delete a scale like 10k if you don't want it)
models=$(cat << 'EOF'
HERE
EOF
)
for model in $models; do
  [[ -z "$model" ]] || go micro full "${model}_0.3k"
  [[ -z "$model" ]] || go small full "${model}_1k"
  [[ -z "$model" ]] || go small full "${model}_3k"
  [[ -z "$model" ]] || go full "${model}_10k"
done


# Evaling
cat << 'EOF' | while read -r model; do [[ -z "$model" ]] || go eval $model; done
d1_code_multiple_languages_1k
d1_code_multiple_languages_3k
d1_code_python_1k
d1_code_python_3k
d1_code_python_10k
d1_code_long_paragraphs_1k
e1_code_fasttext_phi_1k
e1_code_fasttext_phi_3k
e1_code_fasttext_phi_10k
e1_code_fasttext_phi_0.3k
e1_code_fasttext_r1_10k
e1_science_longest_qwq_together_10k
EOF

# Train + eval 
cat << 'EOF' | while read -r model; do [[ -z "$model" ]] || go $model; done
HERE
EOF

# Uploading Models on no internet nodes
upload << 'EOF'
c1_math_nod_4s_10k
c1_math_nod_16s_10k
EOF

# Print out winning jobs
swin 12 | grep -v eval | awk 'NR>1 {job_id=$1; model_name=$3; print model_name}' | grep -v interactive
sacct -X -S "$(date -d "-40 hours" +%F-%H:%M)" -o JobID%10,Partition%9,JobName%70,State | grep "COMPLETED" | grep b2 | awk '{model_name=$3; print model_name}'

# Generate graphs
git switch main
python eval/scripts/get_paper_results.py --substrings c1_ --formatted --scale
python eval/scripts/get_paper_results.py --substrings b1_,openthoughts2 --formatted --scale
python eval/scripts/get_paper_results.py --substrings openthoughts2,no_pipeline --formatted --scale
python eval/scripts/get_paper_results.py --substrings openthoughts2,no_pipeline,bespoke_stratos,openthoughts --formatted --scale
python eval/scripts/get_paper_results.py --substrings b2_,openthoughts2 --formatted --scale
python eval/scripts/get_paper_results.py --substrings b2_math_fasttext,b2_code_fasttext,b2_science_fasttext,openthoughts2 --formatted --scale 

# Clear directories on C2 
ls ~/.cache/huggingface/datasets/
rm -rf ~/.cache/huggingface/datasets/mlfoundations-dev___c1_*
rm  ~/.cache/huggingface/datasets/_home_ryma833h_.cache_huggingface_datasets_mlfoundations-dev___c1*
du -d 2 -h ~/.cache

# Using system - Eval and Train
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/paper/reasoning_medium.yaml --time_limit $DEFAULT_TIME_LIMIT --num_nodes 4 --system system --dataset mlfoundations-dev/meta_chat_reasoning_25_75_system
python eval/distributed/launch_simple.py --tasks AIME24,AMC23,MATH500,MMLUPro,JEEBench,GPQADiamond,LiveCodeBench,CodeElo,CodeForces  --num_shards 4 --system_instruction "detailed thinking on" --model_name mlfoundations-dev/meta_chat_reasoning_0_100_system

# Different sized model
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/paper/reasoning_medium.yaml --time_limit $DEFAULT_TIME_LIMIT --num_nodes 1 --dataset mlfoundations-dev/bespoke_stratos --model_name_or_path Qwen/Qwen2.5-1.5B-Instruct --pretokenize

# Big training jobs on leonardo
python dcft/data_strategies/direct_scale_generator.py --hf "mlfoundations-dev/opencodereasoning" --max-scale 300k && python dcft/data_strategies/direct_scale_generator.py --hf "mlfoundations-dev/openmathreasoning" --max-scale 1000k && python dcft/data_strategies/direct_scale_generator.py --hf "mlfoundations-dev/nemo_nano" --max-scale 1000k

python3 -m hpc.launch --train_config_path dcft/train/hp_settings/paper/reasoning_large.yaml --time_limit $DEFAULT_TIME_LIMIT --num_nodes 128 --dataset mlfoundations-dev/nemo_nano_100k --pretokenize --max_restarts 3 --qos boost_qos_bprod
python3 -m hpc.launch --train_config_path dcft/train/hp_settings/paper/reasoning_large.yaml --time_limit $DEFAULT_TIME_LIMIT --num_nodes 128 --dataset mlfoundations-dev/nemo_nano_100k --pretokenize --max_restarts 3 --qos boost_qos_bprod

# FIG 1 FINAL
python eval/scripts/fig_1_plot.py --substrings OpenThoughts3,openthoughts3,am,nemo_nano,s1,limo --exclude _buggy,_filtered,_ckpts,llama,_32B,Llama,qwen,DCFT,samp,seed,global,filter,ckpt,reformat,camel,swap,_code,_math,_science,s1K,s1k,packing,_leonardo,complete,params,stratos,configs,remove --output fig1_full --evalset full

# SCALING BEST FINAL
python eval/scripts/pipeline_best_scaling.py --substrings a1_math_open2math,b1_math_top_1,b2_math_length,c1_math_0d_16s,e1_math_all_qwq_together,a1_code_code_golf,b1_code_top_2,b2_code_difficulty,c1_code_0d_16s,e1_code_fasttext_qwq_together,a1_science_stackexchange_physics,b1_science_top_2,b2_science_length,c1_science_0d_16s,e1_science_longest_qwq_together --exclude _buggy,_filtered,_ckpts,llama,_32B,Llama,qwen,DCFT,samp,seed,global,filter,ckpt,reformat,camel,swap,packing,_leonardo,complete,params,configs,remove --output pipeline_scaling_best_each_stage --evalset pipeline --pdf

# PLOTS 
python eval/scripts/sec_5_pipeline_scaling.py --substrings openthoughts3_code,nemo_nano_code

python eval/scripts/sec_5_pipeline_scaling.py --substrings openthoughts3_math,openthoughts3_science,openthoughts3_code,nemo_nano_code,nemo_nano_science,nemo_nano_math,no_pipeline_math,no_pipeline_science,no_pipeline_code

python eval/scripts/fig_1_plot.py --substrings openthoughts3 --exclude openthoughts3_math,openthoughts3_science,openthoughts3_code,_buggy,_filtered,_ckpts --output ot3_fg1.png

python eval/scripts/fig_1_plot.py --substrings am --exclude am_math,am_science,am_code,_buggy,_filtered,_ckpts --output am_fg1.png

python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3 --output openthoughts3_all_benchmarks --exclude openthoughts3_math,openthoughts3_science,openthoughts3_code,_buggy,_filtered,_ckpts --evalset full

python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3_math --output openthoughts3_math_all_benchmarks --exclude _buggy,_filtered,_ckpts --evalset full


python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3_math --output openthoughts3_math_all_benchmarks --exclude _buggy,_filtered,_ckpts --evalset full

python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3_math --output openthoughts3_math_HMMT --exclude _buggy,_filtered,_ckpts --evalset full --graphs HMMT

python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3_math,nemo_nano_math --output openthoughts3_math_nemo_nano_math_HMMT --exclude _buggy,_filtered,_ckpts --evalset full --graphs HMMT

python eval/scripts/all_benchmarks_plot.py --substrings openthoughts3_math,nemo_nano_math,openmathreasoning --output openthoughts3_math_nemo_nano_math_openmathreasoning --exclude _buggy,_filtered,_ckpts --evalset full


python eval/scripts/all_benchmarks_plot_og.py --substrings openthoughts3_math,nemo_nano_math,openmathreasoning --output openthoughts3_math_nemo_nano_math_openmathreasoning --exclude _buggy,_filtered,_ckpts --evalset full
