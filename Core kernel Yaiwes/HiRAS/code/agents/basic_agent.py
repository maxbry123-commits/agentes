import os
from smolagents import VLLMModel, CodeAgent

models_dir = "/data"
model_name = "Qwen3-8B"
gpu_count = 1

model = VLLMModel(
    model_id = os.path.join(models_dir, model_name),
    tensor_parallel_size = gpu_count
)

agent = CodeAgent(
    model = model,
    tools = []
)
print(agent.prompt_templates)

papers_dir = "data/papers"
paper_dir = os.path.join(papers_dir, "bridging-data-gaps")
paper_path = os.path.join(paper_dir, "paper.md")

with open(paper_path, "r") as f:
    paper_content = f.read()

template = '''
You are a expericed researcher in the Computer Science domain.
Given a specific paper, your task is to try to reproduce the results in the paper.

Here is the paper you are required to reproduce:

Paper:
{paper}

You should use the tools provided to you to reproduce the results in the paper.

You should output the code in the paper, and excute the code to reproduce the results.

Finally, a report should be generated to summarize the results and compare with the original results to see if the results are reproduced.
'''

agent.run(
    template.format(paper=paper_content)
)

logs_file = "agent.logs"
logs = '\n'.join(agent.memory.get_full_steps())
with open(logs_file, "w") as f:
    f.write(logs)




