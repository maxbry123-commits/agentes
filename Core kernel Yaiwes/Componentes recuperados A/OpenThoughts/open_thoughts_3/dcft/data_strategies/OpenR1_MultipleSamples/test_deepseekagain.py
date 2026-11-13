import os

from datasets import load_dataset

from bespokelabs import curator

from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"
)

# Example message to test the connection
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {
            "role": "user",
            "content": "Write a simple Python function to calculate the factorial of a number.",
        }
    ],
    temperature=0.0,
)

print("Response:", response.choices[0].message.content)


# class Reasoner(curator.LLM):
#     """Curator class for reasoning."""

#     return_completions_object = True

#     def prompt(self, input):
#         """Create a prompt for the LLM to reason about the problem."""
#         return [{"role": "user", "content": input["problem"]}]

#     def parse(self, input, response):
#         """Parse the LLM response to extract reasoning and solution."""
#         input["deepseek_reasoning"] = response["choices"][0]["message"]["reasoning_content"]
#         input["deepseek_solution"] = response["choices"][0]["message"]["content"]
#         return input


# llm = curator.LLM(
#     model_name="deepseek-reasoner",
#     backend="openai_client",
#     generation_params={"temperature": 0.0},
#     backend_params={
#         "max_requests_per_minute": 500,
#         "max_tokens_per_minute": 1_000_000_000,
#         "base_url": "https://api.deepseek.com/",
#         "api_key": os.environ.get("DEEPSEEK_API_KEY"),
#         "require_all_responses": False,
#         "max_retries": 2,
#         "num_clients": 2
#     },
# )
# ds = llm(["hello my banaa"])
# breakpoint()
# ds = load_dataset("mlfoundations-dev/herorun1_code", split="train")
# ds = llm(ds.select(range(50_000, 150_000)))
# # print("REASONING: ", ds[0]["deepseek_reasoning"])
# # print("\n\nSOLUTION: ", ds[0]["deepseek_solution"])
# ds.push_to_hub("mlfoundations-dev/herorun1_code-test_50K_150K")
