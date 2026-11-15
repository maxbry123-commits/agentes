import random

from datasets import Dataset


def prompts_for_evolving_instructions_no_input(
    dataset: Dataset, input_instruction_column: str, output_prompt_column: str
) -> Dataset:
    def f(row: dict) -> dict:
        combined_instruction = row[input_instruction_column].strip()

        prompt = f"""
        Please increase the difficulty of the given programming test question a
        bit.
        You can increase the difficulty using, but not limited to, the following
        methods:
        1. Add new constraints and requirements to the original problem, adding
        approximately 10 additional words.
        2. Replace a commonly used requirement in the programming task with a less
        common and more specific one.
        3. If the original problem can be solved with only a few logical steps,
        please add more reasoning steps.
        4. Provide a piece of erroneous code as a reference to increase
        misdirection.
        5. Propose higher time or space complexity requirements, but please refrain
        from doing so frequently.

        Question:
        {combined_instruction}
        """
        row[output_prompt_column] = random.choice(evolutions)(combined_instruction)
        return row

    return dataset.map(f)
