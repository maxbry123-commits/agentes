from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class RephrasedQuestion(BaseModel):
    rephrased_question: str


class RephraseQuestionMapConfig(BaseModel):
    question_column: str
    output_rephrased_question_column: str


class RephraseQuestionMap(CompletionsMap):
    """
    Given a question, rephrase it.
    """

    def __init__(self, config: dict):
        config = RephraseQuestionMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return RephrasedQuestion

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Prompt model to rephrase questions.
        """
        system_prompt = """
        You are an AI assistant to help me rephrase questions.
        Follow the given examples.

        Question: Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.
        Rephrased question: Starting at 0 on a number line, Kevin Kangaroo aims to reach 1 by hopping only 1/3 of the distance each time. As he gets tired, he continues to hop 1/3 of the remaining distance. After completing five hops, what is the total distance he has covered, expressed as a common fraction?

        Question: If $f(x)=\frac{ax+b}{cx+d}, abcd\not=0$ and $f(f(x))=x$ for all $x$ in the domain of $f$, what is the value of $a+d$?
        Rephrased question: Given that $f(x) = \frac{ax + b}{cx + d}$, with all variables not equal to 0, and $f(f(x)) = x$ for all x within the domain of f, what is the value of $a + d$?

        Question: Sam bought a dozen boxes, each with 30 highlighter pens inside, for $10 each box. He rearranged five of these boxes into packages of six highlighters each and sold them for $3 per package. He sold the rest of the highlighters separately at the rate of three pens for $2. How much profit did he make in total, in dollars?
        Rephrased question: Sam purchased 12 boxes, each containing 30 highlighter pens, at $10 per box. He repackaged five of these boxes into sets of six highlighters and sold them for $3 per set. He sold the remaining highlighters individually at a rate of three pens for $2. What is the total profit he made in dollars?

        Question: The quadratic equation $x^2+mx+n=0$ has roots that are twice those of $x^2+px+m=0,$ and none of $m,$ $n,$ and $p$ is zero. What is the value of $n/p?$
        Rephrased question: For the quadratic equation $x^2 + mx + n = 0$, the roots are twice the roots of $x^2 + px + m = 0$. None of the variables $m$, $n$, and $p$ are zero. What is the value of $n/p$?

        Question: Find the mean of all solutions for $x$ when $x^3 + 3x^2 - 10x = 0$.
        Rephrased question: What is the average of all the solutions for $x$ in the equation $x^3 + 3x^2 - 10x = 0$?
      
        Question: Angelo and Melanie want to plan how many hours over the next week they should study together for their test next week. They have 2 chapters of their textbook to study and 4 worksheets to memorize. They figure out that they should dedicate 3 hours to each chapter of their textbook and 1.5 hours for each worksheet. If they plan to study no more than 4 hours each day, how many days should they plan to study total over the next week if they take a 10-minute break every hour, include 3 10-minute snack breaks each day, and 30 minutes for lunch each day?
        Rephrased question: Angelo and Melanie need to study 2 chapters in their textbook and 4 worksheets for their upcoming test. They have planned to dedicate 3 hours for each chapter and 1.5 hours for each worksheet. They can study for a maximum of 4 hours each day, taking into account 10-minute breaks every hour, 3 10-minute snack breaks per day, and 30 minutes for lunch. How many days do they need to study in total over the next week to complete their study plan?

        Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?
        Rephrased question: Determine the area of the region described by the equation $x^2+y^2 - 7 = 4y-14x+3$?

        Question: If $x^2+y^2=1$, what is the largest possible value of $|x|+|y|$?
        Rephrased question: What is the maximum value possible for |x| + |y| if x^2 + y^2 = 1?

        Question: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
        Rephrased question: If Leah had 32 chocolates and her sister had 42, and they both consumed 35 chocolates, what is the total number of chocolates that they have left?

        Question: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
        Rephrased question: What is the amount of money that Olivia has left after purchasing five bagels for $3 each, if she initially had $23?
        """
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {dataset_row[self.config.question_column]}",
            },
        ]

    @staticmethod
    def _is_numeric(s: str) -> bool:
        """Check if string contains a number."""
        return any(char.isdigit() for char in s)

    def parse(self, dataset_row: dict, response: RephrasedQuestion):
        """
        Parse the rephrased question.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            The numerical answer if it is numeric, otherwise an empty list.
        """
        dataset_row[self.config.output_rephrased_question_column] = (
            response.rephrased_question
        )
        return dataset_row
