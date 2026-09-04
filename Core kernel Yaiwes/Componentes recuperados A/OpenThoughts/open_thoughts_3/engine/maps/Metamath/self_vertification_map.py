import logging
import multiprocessing as mp
import zipfile

import nltk
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

# Needed for sent_tokenize to work.
try:

    def download_nltk_punkt():
        nltk.download("punkt")

    # set timeout to 10 seconds
    p = mp.Process(target=download_nltk_punkt)
    p.start()
    p.join(10)
    if p.is_alive():
        p.terminate()
    logging.debug("Downloaded NLTK punkt tokenizer.")

except zipfile.BadZipFile as e:
    logging.warning(
        f"Failed to download NLTK punkt_tab. This is most likely due to a race condition and "
        f"some other process downloading the data at the same time. This is fine. "
        f"Original error: {e}",
    )
except FileExistsError:
    # It's fine if punkt's already downloaded.
    logging.debug("Punkt tokenizer already downloaded.")
    pass

except Exception as e:
    logging.error(f"Failed to download NLTK punkt_tab. Error: {e}")


class DeclarativeStatement(BaseModel):
    statement: str


class SelfVerificationMapConfig(BaseModel):
    question_column: str
    answer_column: str


class SelfVerificationMap(CompletionsMap):
    """
    Use the self-verification method from MetaMath to find and rephrase the original question
    into a declarative statement and then add a question to the new output column.
    """

    def __init__(self, config: dict):
        config = SelfVerificationMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return DeclarativeStatement

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Prompt model to rewrite questions into declarative statements.
        """
        system_prompt = """
        You are an AI assistant to help me rewrite question into a declarative statement when its answer is provided.
        Follow the given examples and rewrite the question.

        Question: What is the largest possible value of $|x|+|y|$? The answer is \sqrt{2}.
        Result: {"statement": "The largest possible value of $|x| + |y|$ is \sqrt{2}."}

        Question: How many trees did the grove workers plant today? The answer is 6.
        Result: {"statement": "The grove workers planted 6 trees today."}

        Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$? The answer is 63\pi.
        Result: {"statement": "The area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$ is 63\pi."}

        Question: How many computers are now in the server room? The answer is 29.
        Result: {"statement": "There are 29 computers now in the server room."}
        """
        # Take the last sentence of the question (which is the question itself)
        # and rephrase it into a declarative statement.
        sentences = sent_tokenize(dataset_row[self.config.question_column])
        last_sentence = sentences[-1]

        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {last_sentence}. The answer is {dataset_row[self.config.answer_column]}.",
            },
        ]

    def parse(self, dataset_row: dict, response: DeclarativeStatement):
        """
        Parse the response from the completions model. Basically, we remove the
        question (which is the last sentence of the question) and replace it with
        the declarative statement.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            The dataset row with the new question.
        """
        base_sentences = sent_tokenize(dataset_row[self.config.question_column])

        # Get everything upto the last sentence of the question since we're removing it. Then merge the
        # restated declarative statement with the rest. Example:
        #
        # Question: Suppose |x| and |y| are nonnegative real numbers. What is the largest possible value of $|x|+|y|$? The answer is \sqrt{2}.
        # Response: The largest possible value of $|x| + |y|$ is \sqrt{2}.
        # New question: Suppose |x| and |y| are nonnegative real numbers. The largest possible value of $|x| + |y|$ is \sqrt{2}.
        # What is the value of the unknown variable X?

        base_text = " ".join(base_sentences[:-1])
        dataset_row[self.config.question_column] = (
            f"{base_text} {response.statement} What is the value of the unknown variable X?"
        )
        dataset_row["method"] = "self_verification"
        return dataset_row
