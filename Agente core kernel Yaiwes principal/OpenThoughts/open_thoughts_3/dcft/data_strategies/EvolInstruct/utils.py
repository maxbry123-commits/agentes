import random

from datasets import Dataset

breadth_base_instruction = "I want you act as a Prompt Creator.\r\n\
Your goal is to draw inspiration from the #Given Prompt# to create a brand new prompt.\r\n\
This new prompt should belong to the same domain as the #Given Prompt# but be even more rare.\r\n\
The LENGTH and complexity of the #Created Prompt# should be similar to that of the #Given Prompt#.\r\n\
The #Created Prompt# must be reasonable and must be understood and responded by humans.\r\n\
'#Given Prompt#', '#Created Prompt#', 'given prompt' and 'created prompt' are not allowed to appear in #Created Prompt#\r\n"

depth_base_instruction = "I want you act as a Prompt Rewriter.\r\n \
Your objective is to rewrite a given prompt into a more complex version to make those famous AI systems (e.g., chatgpt and GPT4) a bit harder to handle.\r\n \
But the rewritten prompt must be reasonable and must be understood and responded by humans.\r\n \
Your rewriting cannot omit the non-text parts such as the table and code in #The Given Prompt#:. Also, please do not omit the input in #The Given Prompt#. \r\n \
You SHOULD complicate the given prompt using the following method: \r\n\
{} \r\n\
You should try your best not to make the #Rewritten Prompt# become verbose, #Rewritten Prompt# can only add 10 to 20 words into #The Given Prompt#. \r\n\
'#The Given Prompt#', '#Rewritten Prompt#', 'given prompt' and 'rewritten prompt' are not allowed to appear in #Rewritten Prompt#\r\n"


def createBreadthPrompt(instruction):
    prompt = breadth_base_instruction
    prompt += "#Given Prompt#: \r\n {} \r\n".format(instruction)
    prompt += "#Created Prompt#:\r\n"
    return prompt


def createConstraintsPrompt(instruction):
    prompt = depth_base_instruction.format(
        "Please add one more constraints/requirements into #The Given Prompt#'"
    )
    prompt += "#The Given Prompt#: \r\n {} \r\n".format(instruction)
    prompt += "#Rewritten Prompt#:\r\n"
    return prompt


def createDeepenPrompt(instruction):
    prompt = depth_base_instruction.format(
        "If #The Given Prompt# contains inquiries about certain issues, the depth and breadth of the inquiry can be increased."
    )
    prompt += "#The Given Prompt#: \r\n {} \r\n".format(instruction)
    prompt += "#Rewritten Prompt#:\r\n"
    return prompt


def createConcretizingPrompt(instruction):
    prompt = depth_base_instruction.format(
        "Please replace general concepts with more specific concepts."
    )
    prompt += "#The Given Prompt#: \r\n {} \r\n".format(instruction)
    prompt += "#Rewritten Prompt#:\r\n"
    return prompt


def createReasoningPrompt(instruction):
    prompt = depth_base_instruction.format(
        "If #The Given Prompt# can be solved with just a few simple thinking processes, you can rewrite it to explicitly request multiple-step reasoning."
    )
    prompt += "#The Given Prompt#: \r\n {} \r\n".format(instruction)
    prompt += "#Rewritten Prompt#:\r\n"
    return prompt


evolutions = [
    createConstraintsPrompt,
    createDeepenPrompt,
    createConcretizingPrompt,
    createReasoningPrompt,
    createBreadthPrompt,
]


def prompts_for_evolving_instructions(
    dataset: Dataset,
    input_instruction_column: str,
    input_input_column: str,
    output_prompt_column: str,
) -> Dataset:
    def f(row: dict) -> dict:
        combined_instruction = (
            row[input_instruction_column].strip()
            + "\r\n"
            + row[input_input_column].strip()
        )
        row[output_prompt_column] = random.choice(evolutions)(combined_instruction)
        return row

    return dataset.map(f)


def prompts_for_evolving_instructions_no_input(
    dataset: Dataset, input_instruction_column: str, output_prompt_column: str
) -> Dataset:
    def f(row: dict) -> dict:
        combined_instruction = row[input_instruction_column].strip()
        row[output_prompt_column] = random.choice(evolutions)(combined_instruction)
        return row

    return dataset.map(f)


def codeevol_prompts_for_evolving_instructions_no_input(
    dataset: Dataset, input_instruction_column: str, output_prompt_column: str
) -> Dataset:
    def f(row: dict) -> dict:
        combined_instruction = row[input_instruction_column].strip()
        prompt = f"""
        Please increase the difficulty of the given programming test question a
        bit.
        You can increase the difficulty using, but not limited to, the following
        methods:
        Add new constraints and requirements to the original problem, adding
        approximately 10 additional words.
        Replace a commonly used requirement in the programming task with a less
        common and more specific one.
        If the original problem can be solved with only a few logical steps,
        please add more reasoning steps.
        Provide a piece of erroneous code as a reference to increase
        misdirection.
        Propose higher time or space complexity requirements, but please refrain
        from doing so frequently.


        Question: {combined_instruction}

        Please give me your revised question. Do not say anything else besides the question itself. Do not mention phrases such as 'Revised Question:' or 'Here is a question'. 
        """
        row[output_prompt_column] = prompt
        return row

    return dataset.map(f)
