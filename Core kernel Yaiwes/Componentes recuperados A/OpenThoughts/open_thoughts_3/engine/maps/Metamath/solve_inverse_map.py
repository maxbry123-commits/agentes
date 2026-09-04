from typing import Union

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class Answer(BaseModel):
    solution: str
    final_answer: Union[str, float, int]


class SolveInverseMapConfig(BaseModel):
    inverse_question_column: str
    inverse_answer_column: str
    output_predicted_answer_column: str


class SolveInverseMap(CompletionsMap):
    """
    Solve the inverse question and return all attempts that match
    the ground truth inverse answer.
    """

    def __init__(self, config: dict):
        config = SolveInverseMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return Answer

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Prompt model to solve the inverse questions.
        """
        system_prompt = """
        You are an AI assistant to help me solve math problem.
        I first give you an original question with an unknown variable X, You help me determine the value of X.
        Follow the given examples and answer the question.

        Question: Randy has 60 mango trees on his farm. He also has X less than half as many coconut trees as mango trees. Randy has 85 trees in all on his farm. What is the value of unknown variable X?
        A: Let's think step by step.
        Solution: To solve this problem, we need to set up an equation based on the given information and then solve for the unknown variable X.
        Let's break down the information given:
        Randy has 60 mango trees.
        Randy has X less than half as many coconut trees as mango trees.
        Randy has 85 trees in total.
        We can set up the equation as follows:
        Number of mango trees + Number of coconut trees = Total number of trees
        60 + (60/2 - X) = 85
        Let's simplify and solve for X:
        60 + 30 - X = 85
        90 - X = 85
        To isolate X, we subtract 90 from both sides of the equation:
        90 - X - 90 = 85 - 90
        -X = -5
        Finally, we multiply both sides of the equation by -1 to solve for X:
        X = 5
        Final answer: 5

        Question: Joy can read 8 pages of a book in 20 minutes. It will take her 5 hours to read X pages. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to determine the value of X, which represents the number of pages Joy will read in 5 hours.
        We know that Joy can read 8 pages in 20 minutes. Let's find out how many pages she can read in 1 minute:
        8 pages / 20 minutes = 0.4 pages per minute
        Now, let's calculate how many pages Joy can read in 5 hours:
        5 hours = 5 * 60 = 300 minutes
        0.4 pages per minute * 300 minutes = 120 pages
        Therefore, the value of the unknown variable X is 120. Joy will read 120 pages in 5 hours.
        Final answer: 120

        Question: In a truck, there are 26 pink hard hats, 15 green hard hats, and 24 yellow hard hats. If Carl takes away 4 pink hard hats, and John takes away X pink hard hats and twice as many green hard hats as the number of pink hard hats that he removed, The total number of hard hats that remained in the truck is 43. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to set up an equation based on the given information and then solve for the unknown variable X.
        Let's break down the information given:
        Number of pink hard hats: 26 - 4 (Carl takes away 4 pink hard hats)
        Number of green hard hats: 15
        Number of yellow hard hats: 24
        Total number of hard hats: 43
        We can set up the equation as follows:
        Number of pink hard hats - (X + 2X) + Number of green hard hats + Number of yellow hard hats = Total number of hard hats
        26 - 4 - (X + 2X) + 15 + 24 = 43
        Let's simplify and solve for X:
        22 - 3X + 15 + 24 = 43
        61 - 3X = 43
        To isolate X, we subtract 61 from both sides of the equation:
        61 - 3X - 61 = 43 - 61
        -3X = -18
        Finally, we divide both sides of the equation by -3 to solve for X:
        X = -18 / -3
        X = 6
        Final answer: 6

        Question: Each bird eats 12 beetles per day, each snake eats 3 birds per day, and each jaguar eats 5 snakes per day. If there are X jaguars in a forest, 1080 beetles are eaten each day. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to determine the value of X, which represents the number of jaguars in the forest.
        Let's break down the information given:
        Number of beetles eaten by each bird per day: 12
        Number of birds eaten by each snake per day: 3
        Number of snakes eaten by each jaguar per day: 5
        Total number of beetles eaten per day: 1080
        We can set up the equation as follows:
        Number of beetles eaten by each bird per day * Number of birds eaten by each snake per day * Number of snakes eaten by each jaguar per day * Number of jaguars = Total number of beetles eaten per day
        12 * 3 * 5 * X = 1080
        Let's simplify and solve for X:
        12 * 3 * 5 * X = 1080
        180X = 1080
        To isolate X, we divide both sides of the equation by 180:
        180X / 180 = 1080 / 180
        X = 6
        Final answer: 6

        Question: It's Ava's birthday party. Her parents bought a unicorn piñata for $13 and filled it with all of her favorite treats. They bought 4 bags of Reese's for $9 per bag, 3 bags of Snickers for $5 per bag, and 5 bags of Skittles for X per bag. The unicorn piñata and the treats cost 99 altogether. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to determine the value of X, which represents the cost of each bag of Skittles.
        Let's break down the information given:
        Cost of the unicorn piñata: $13
        Number of bags of Reese's: 4
        Cost per bag of Reese's: $9
        Number of bags of Snickers: 3
        Cost per bag of Snickers: $5
        Number of bags of Skittles: 5
        Cost per bag of Skittles: X
        Total cost of the unicorn piñata and treats: $99
        We can set up the equation as follows:
        Cost of the unicorn piñata + (Number of bags of Reese's * Cost per bag of Reese's) + (Number of bags of Snickers * Cost per bag of Snickers) + (Number of bags of Skittles * Cost per bag of Skittles) = Total cost of the unicorn piñata and treats
        $13 + (4 * $9) + (3 * $5) + (5 * X) = $99
        Let's simplify and solve for X:
        $13 + $36 + $15 + 5X = $99
        $64 + 5X = $99
        To isolate X, we subtract $64 from both sides of the equation:
        $64 - $64 + 5X = $99 - $64
        5X = $35
        To solve for X, we divide both sides of the equation by 5:
        X = $35 / 5
        X = $7
        Final answer: 7

        Question: Liza bought X kilograms of butter to make cookies. She used one-half of it for chocolate chip cookies, one-fifth of it for peanut butter cookies, and one-third of the remaining butter for sugar cookies. There are 2 kilograms of butter left after making those three kinds of cookies. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to determine the value of X, which represents the initial amount of butter Liza bought in kilograms.
        Let's break down the information given:
        Amount of butter used for chocolate chip cookies: 1/2X
        Amount of butter used for peanut butter cookies: 1/5X
        Amount of butter used for sugar cookies: 1/3 * (X - (1/2X + 1/5X))
        Amount of butter left: 2 kilograms
        We can set up the equation as follows:
        Amount of butter used for chocolate chip cookies + Amount of butter used for peanut butter cookies + Amount of butter used for sugar cookies + Amount of butter left = Initial amount of butter
        1/2X + 1/5X + 1/3 * (X - (1/2X + 1/5X)) + 2 = X
        Let's simplify and solve for X:
        (5/10)X + (2/10)X + (1/3)(X - (7/10)X) + 2 = X
        (7/10)X + (1/3)(3/10)X + 2 = X
        (7/10)X + (1/10)X + 2 = X
        (8/10)X + 2 = X
        To isolate X, we subtract (8/10)X from both sides of the equation:
        (8/10)X - (8/10)X + 2 = X - (8/10)X
        2 = (2/10)X
        To solve for X, we multiply both sides of the equation by 10/2:
        2 * (10/2) = (2/10)X * (10/2)
        10 = X
        Final answer: 10

        Question: Carly collected X starfish with 5 arms each and one seastar with 14 arms. The animals she collected have 49 arms in total. What is the value of unknown variable X?
        A: Let's think step by step.
        To solve this problem, we need to determine the value of X, which represents the number of starfish with 5 arms that Carly collected.
        Let's break down the information given:
        Number of starfish with 5 arms: X
        Number of seastars with 14 arms: 1
        Total number of arms: 49
        We can set up the equation as follows:
        Number of starfish with 5 arms * Number of arms per starfish + Number of seastars with 14 arms * Number of arms per seastar = Total number of arms
        X * 5 + 1 * 14 = 49
        Let's simplify and solve for X:
        5X + 14 = 49
        To isolate X, we subtract 14 from both sides of the equation:
        5X + 14 - 14 = 49 - 14
        5X = 35
        To solve for X, we divide both sides of the equation by 5:
        X = 35 / 5
        X = 7
        Final answer: 7

        Question: On a map, a 12-centimeter length represents $X$ kilometers.  How many kilometers does a 17-centimeter length represent? If we know the answer to the above question is 102, what is the value of unknown variable $X$?
        A: Let's think step by step.
        Solution: We know that on the map, a 12-centimeter length represents $X$ kilometers.
        To find out how many kilometers a 17-centimeter length represents, we can set up a proportion using the given information:
        12 centimeters / $X$ kilometers = 17 centimeters / 102 kilometers
        We can cross-multiply and solve for $X$:
        12 * 102 = 17 * $X$
        1224 = 17 * $X$
        Dividing both sides by 17, we get:
        $X$ = 72
        The value of X is 72.
        Final answer: 72

        Question: If the sum of the squares of nonnegative real numbers $a,b,$ and $c$ is $39$, and $ab + bc + ca = X$, then what is the sum of $a,b,$ and $c$? If we know the answer to the above question is 9, what is the value of unknown variable $X$?
        A: Let's think step by step.
        Solution: We are given that the sum of the squares of nonnegative real numbers $a$, $b$, and $c$ is $39$, and $ab + bc + ca = X$.
        To find the sum of $a$, $b$, and $c$, we need to determine the value of $X$.
        We can start by using the given information to set up an equation.
        We know that $(a^2 + b^2 + c^2) = 39$ and $ab + bc + ca = X$.
        We can rewrite the equation $(a^2 + b^2 + c^2)$ as $(a^2 + b^2 + c^2 + 2ab + 2bc + 2ca - 2ab - 2bc - 2ca)$.
        Using this, we can expand the equation as follows:
        $(a^2 + b^2 + c^2 + 2ab + 2bc + 2ca - 2ab - 2bc - 2ca) = 39$
        Simplifying this equation gives us:
        $(a + b + c)^2 = 39 + 2(ab + bc + ca)$
        $(a + b + c)^2 = 39 + 2X$
        Now, we know that the sum of $a$, $b$, and $c$ is the square root of $(a + b + c)^2$. Let's call this sum $S$.
        $S = \sqrt{(a + b + c)^2}$
        $S = \sqrt{39 + 2X}$
        Given that the sum of $a$, $b$, and $c$ is 9, we can set up the equation:
        $9 = \sqrt{39 + 2X}$
        To solve for $X$, we can square both sides of the equation:
        $81 = 39 + 2X$
        Subtracting 39 from both sides, we get:
        $42 = 2X$
        Dividing both sides by 2, we find:
        $X = 21$
        Final answer: 21

        Question: The mean of $5,8$ and $17$ is equal to the mean of $X$ and $y$. What is the value of $y$? If we know the answer to the above question is 8, what is the value of unknown variable X?
        A: Let's think step by step.
        Solution: We are given that the mean of 5, 8, and 17 is equal to the mean of $X$ and $y$.
        To find the value of $y$, we need to determine the value of $X$.
        The mean of a set of numbers is found by summing all the numbers and dividing by the total count.
        For the given set of numbers, the mean is:
        (5 + 8 + 17) / 3 = 30 / 3 = 10
        Since the mean of $X$ and $y$ is also 10, we can set up the equation:
        (X + y) / 2 = 10
        Multiplying both sides by 2, we get:
        X + y = 20
        Given that the value of $y$ is 8, we can substitute it into the equation:
        X + 8 = 20
        Subtracting 8 from both sides, we find:
        X = 12
        Final answer: 12

        Question: A taxi ride costs \\$1.50$ plus $\\$0.25$ per mile traveled.  How much, in dollars, does a $X$ mile taxi ride cost? If we know the answer to the above question is 2.75, what is the value of unknown variable X?
        A: Let's think step by step.
        Solution: We are given that a taxi ride costs $1.50 plus $0.25 per mile traveled.
        To find the cost of a $X$ mile taxi ride, we can set up an equation using the given information.
        The equation can be written as:
        Cost = $1.50 + $0.25 * X
        We are given that the cost is $2.75, so we can substitute this value into the equation:
        $2.75 = $1.50 + $0.25 * X
        Now we can solve for $X$.
        Subtracting $1.50 from both sides of the equation, we get:
        $2.75 - $1.50 = $0.25 * X
        $1.25 = $0.25 * X
        Dividing both sides of the equation by $0.25, we find:
        X = 5
        Final answer: 12

        Question: How many ways are there to put 5 balls in $X$ boxes if the balls are not distinguishable but the boxes are? If we know the answer to the above question is 6, what is the value of unknown variable $X$?
        A: Let's think step by step.
        Solution: We want to find the value of $X$ in the given situation.
        We are told that the balls are not distinguishable, but the boxes are.
        This means that the arrangement of balls in the boxes does not matter, and we only need to consider the number of balls in each box.
        To solve this, let's use the concept of stars and bars.
        We can imagine the balls as stars and the boxes as bars.
        The number of ways to distribute the balls among the boxes is equal to the number of ways to arrange the stars and bars.
        In this case, we have 5 balls and $X$ boxes.
        So, we need to distribute the 5 balls among $X$ boxes using stars and bars.
        The number of ways to arrange the stars and bars can be calculated using the formula:
        Number of ways = (Number of objects + Number of gaps) choose (Number of gaps)
        In this case, the number of objects is 5 (balls) and the number of gaps is $X-1$ (the spces between the bars).
        We are given that the number of ways is 6, so we can write:
        6 = (5 + $X-1$) choose ($X-1$)
        Simplifying, we have:
        6 = (4 + $X$) choose ($X-1$)
        To find the value of $X$, we can try different values and solve for $X$.
        Let's start with $X = 2$:
        6 = (4 + 2) choose (2-1)
        6 = 6 choose 1
        6 = 6
        The equation holds true for $X = 2$.
        Final solution: 2
        """

        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {dataset_row[self.config.inverse_question_column]} \n A: Let's think step by step.",
            },
        ]

    def parse(self, dataset_row: dict, response: Answer):
        """
        Parse the response from the completions model and keep
        predicted answers that match the ground truth inverse
        answer.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            A list of dictionaries with the original question, answer, and the inverse question and answer.
        """
        cleaned_predicted_answer = str(response.final_answer).replace("$", "")
        cleaned_ground_truth_answer = dataset_row[
            self.config.inverse_answer_column
        ].replace("$", "")
        if cleaned_predicted_answer == cleaned_ground_truth_answer:
            dataset_row[self.config.output_predicted_answer_column] = response.solution
            return [dataset_row]
        return []
