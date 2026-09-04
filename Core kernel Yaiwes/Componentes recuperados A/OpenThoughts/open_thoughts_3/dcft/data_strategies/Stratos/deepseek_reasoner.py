from bespokelabs import curator

from dcft.data_strategies.Stratos.prompts import SKY_T1_SYSTEM_PROMPT


class DeepSeekReasoner(curator.LLM):
    return_completions_object = True

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [
            {"role": "system", "content": SKY_T1_SYSTEM_PROMPT},
            {"role": "user", "content": input["problem"]},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        return {
            "problem": input["problem"],
            "reasoning": response["choices"][0]["message"]["reasoning_content"],
            "deepseek_solution": response["choices"][0]["message"]["content"],
            "ground_truth_solution": input["solution"],
        }
