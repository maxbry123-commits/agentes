import os
import time
import subprocess
import yaml
import argparse
import json
import logging
from smolagents import VLLMModel, OpenAIServerModel
from agents.manager_agent import ManagerAgent
from agents.utils import calc_cost

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data/")
    
    parser.add_argument("--output_dir", type=str, default="output/")
    parser.add_argument("--run_dir", type=str, default=None)
    
    parser.add_argument("--base_env_name", type=str, default="ExpBase")
    parser.add_argument("--exp_env_name", type=str, default="Temp4Exp-dpsk-v3")
    
    parser.add_argument("--model", type=str, default="deepseek-v3")
    parser.add_argument("--models_dir", type=str, default="/models")
    parser.add_argument("--gpu_count", type=int, default=8)
    parser.add_argument("--step_multiplier", type=int, default=1)
    
    parser.add_argument("--prompt_base_dir", type=str, default="prompts/")
    parser.add_argument("--benchmark", type=str, default="paperbench")
    
    parser.add_argument("--split", type=str, default="debug")
    parser.add_argument("--splits_dir", type=str, default="splits/")
    return parser.parse_args()

def get_model(args):
    if args.model == "deepseek-v3":
        return "deepseek-v3", OpenAIServerModel(
            model_id="DeepSeek-V3_1-Terminus",
            api_base="API_BASE_URL",
            api_key = "EMPTY"
        )
        
    elif args.model == "deepseek-r1":
        return "deepseek-r1", OpenAIServerModel(
            model_id="DeepSeek-R1",
            api_base="API_BASE_URL",
            api_key = "EMPTY"
        )
        
    elif args.model == "qwen3-480b":
        return "qwen3-480b", OpenAIServerModel(
            model_id="Qwen3-480B",
            api_base="API_BASE_URL",
            api_key = "EMPTY",
            requests_per_minute = 60.0
        )
        
    else:
        logger.info(f"=====Loading model {args.model}=====")
        model_alias = args.model.lower()
        model = VLLMModel(
            model_id = f"{args.models_dir}/{args.model}",
            model_kwargs = {
                "tensor_parallel_size": args.gpu_count,
                "max_model_len": 128000,
                "enforce_eager": True,
                "rope_scaling": {"factor": 4.0, "original_max_position_embeddings": 32768, "rope_type": "yarn"}
            }
        )
        return model_alias, model

def main():

    bash_path = os.path.abspath(".")
    args = parse_args()
    
    model_alias, model = get_model(args)

    if args.run_dir is None:
        current_time = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        args.run_dir = os.path.join(args.output_dir, args.benchmark, model_alias, current_time)
        if not os.path.exists(args.run_dir):
            os.makedirs(args.run_dir)
    else:
        args.run_dir = os.path.join(args.output_dir, args.benchmark, model_alias, args.run_dir)
    
    prompt_dir = os.path.join(args.prompt_base_dir, args.benchmark)

    task_prompt_path = os.path.join(prompt_dir, "task_prompt.yaml")
    with open(task_prompt_path, "r") as f:
        data = yaml.safe_load(f)
        prompt = data['prompt']
    logger.info(prompt)

    if args.benchmark == "paperbench":
        split_path = os.path.join(args.splits_dir, f"{args.split}.txt")

        with open(split_path, "r") as f:
            papers = [line.strip() for line in f if line.strip()]

        for paper in papers:
            dir_path = os.path.join(args.data_dir, args.benchmark, paper)
            if os.path.isdir(dir_path):
                cur_dir = os.path.join(args.run_dir, paper)
                if os.path.exists(cur_dir):
                    continue
                
                logger.info(f"=====Reproducing {paper}=====")
                if args.exp_env_name != args.base_env_name:
                    try:
                        logger.info(f"=====Creating environment {args.exp_env_name}=====")
                        subprocess.run(f"conda create -n {args.exp_env_name} --clone {args.base_env_name}", 
                                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception as e:
                        logger.info(f"=====Error: {e} when creating environment {args.exp_env_name}=====")
                        break
                os.makedirs(cur_dir)
            
                subprocess.run(f"cp {dir_path}/paper.md {cur_dir}/", shell=True, cwd=bash_path)
                if os.path.exists(os.path.join(dir_path, "addendum.md")):
                    subprocess.run(f"cp {dir_path}/addendum.md {cur_dir}/", shell=True, cwd=bash_path)
                    
                try:
                    agent = ManagerAgent(model=model, 
                                        prompt_dir=prompt_dir, 
                                        root_dir=cur_dir, 
                                        step_multiplier=args.step_multiplier,
                                        env_name=args.exp_env_name)
                    
                    agent.run(prompt, max_steps=32 * args.step_multiplier)
                except Exception as e:
                    logger.error(f"=====Error when running paper {paper}: {e}=====")
                    if args.exp_env_name != args.base_env_name:
                        logger.info(f"=====Removing environment {args.exp_env_name}=====")
                        subprocess.run(f"conda remove -n {args.exp_env_name} --all -y", 
                                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                
                agent.print_log()
                if args.exp_env_name != args.base_env_name:
                    logger.info(f"=====Removing environment {args.exp_env_name}=====")
                    subprocess.run(f"conda remove -n {args.exp_env_name} --all -y", 
                                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                input_tokens = 0
                output_tokens = 0
                cost_dir = os.path.join(cur_dir, "cost")
                for file in os.listdir(cost_dir):
                    if file.endswith(".json"):
                        with open(os.path.join(cost_dir, file), "r") as f:
                            cost = json.load(f)
                            input_tokens += cost["input"]
                            output_tokens += cost["output"]
                cost_summary = {
                    "input": input_tokens,
                    "output": output_tokens,
                    "cost": calc_cost(model_alias, input_tokens, output_tokens)
                }
                with open(os.path.join(cur_dir, "cost.json"), "w+") as f:
                    json.dump(cost_summary, f, indent=2)
            
        paper_count = 0
        total_cost = 0.0
        total_input = 0
        total_output = 0
        for paper in papers:
            cur_dir = os.path.join(args.run_dir, paper)
            if not os.path.exists(cur_dir):
                continue
            
            cost_file = os.path.join(cur_dir, "cost.json")
            if not os.path.exists(cost_file):
                if not os.path.exists(os.path.join(cur_dir, "cost")):
                    logger.info(f"=====Cost file not found for {paper}=====")
                    continue
                else:
                    input_tokens = 0
                    output_tokens = 0
                    cost_dir = os.path.join(cur_dir, "cost")
                    for file in os.listdir(cost_dir):
                        if file.endswith(".json"):
                            with open(os.path.join(cost_dir, file), "r") as f:
                                cost = json.load(f)
                                input_tokens += cost["input"]
                                output_tokens += cost["output"]
                    cost_summary = {
                        "input": input_tokens,
                        "output": output_tokens,
                        "cost": calc_cost(model_alias, input_tokens, output_tokens)
                    }
                    with open(cost_file, "w+") as f:
                        json.dump(cost_summary, f, indent=2)
            
            with open(cost_file, "r") as f:
                cost = json.load(f)
                total_cost += cost["cost"]
                total_input += cost["input"]
                total_output += cost["output"]
                
                paper_count += 1
        
        cost_summary = {
            "total_input": total_input,
            "total_output": total_output,
            "total_cost": total_cost,
            
            "avg_input": total_input / paper_count,
            "avg_output": total_output / paper_count,
            "avg_cost": total_cost / paper_count,
        }
        cost_file = os.path.join(args.run_dir, "cost.json")
        with open(cost_file, "w+") as f:
            json.dump(cost_summary, f, indent=2)
                    
    elif args.benchmark == "paper2code":
        paper_dir = os.path.join(args.data_dir, args.benchmark)
        
        info_path = os.path.join(paper_dir, "dataset_info.json")
        with open(info_path, "r") as f:
            info = json.load(f)
        
        for conf in info.keys():
            conf_dir = os.path.join(paper_dir, conf)
            
            for paper_info in info[conf]:
                paper = paper_info['repo_name']
                cur_dir = os.path.join(args.run_dir, conf, paper)
                if os.path.exists(cur_dir):
                    continue
                
                logger.info(f"=====Reproducing {paper}=====")
                if args.exp_env_name != args.base_env_name:
                    try:
                        logger.info(f"=====Creating environment {args.exp_env_name}=====")
                        subprocess.run(f"conda create -n {args.exp_env_name} --clone {args.base_env_name}", 
                                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception as e:
                        logger.info(f"=====Error: {e} when creating environment {args.exp_env_name}=====")
                        break
                    
                os.makedirs(cur_dir, exist_ok=True)
                subprocess.run(f"cp {conf_dir}/{paper}_cleaned.json {cur_dir}/paper.json", shell=True, cwd=bash_path)
                
                try:
                    agent = ManagerAgent(model=model, 
                                            prompt_dir=prompt_dir, 
                                            root_dir=cur_dir, 
                                            step_multiplier=args.step_multiplier,
                                            env_name=args.exp_env_name)
                    
                    agent.run(prompt, max_steps=32 * args.step_multiplier)
                except Exception as e:
                    logger.error(f"=====Error when running paper {paper}: {e}=====")
                    if args.exp_env_name != args.base_env_name:
                        logger.info(f"=====Removing environment {args.exp_env_name}=====")
                        subprocess.run(f"conda remove -n {args.exp_env_name} --all -y", 
                                        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                
                agent.print_log()
                if args.exp_env_name != args.base_env_name:
                    logger.info(f"=====Removing environment {args.exp_env_name}=====")
                    subprocess.run(f"conda remove -n {args.exp_env_name} --all -y", 
                                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
       
if __name__ == "__main__":
    main()