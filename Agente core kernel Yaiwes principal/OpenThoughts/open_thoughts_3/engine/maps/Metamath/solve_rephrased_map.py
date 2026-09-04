from typing import Union

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class Answer(BaseModel):
    solution: str
    final_answer: Union[str, float, int]


class SolveRephraseMapConfig(BaseModel):
    rephrased_question_column: str
    answer_column: str
    output_predicted_answer_column: str


class SolveRephraseMap(CompletionsMap):
    """
    Solve the rephrased question and return all attempts that match
    the ground truth answer.
    """

    def __init__(self, config: dict):
        config = SolveRephraseMapConfig(**config)
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
        Question: A math teacher requires Noelle to do one homework assignment for each of the first five homework points she wants to earn; for each of the next five homework points, she needs to do two homework assignments; and so on, so that to earn the $n^{\text{th}}$ homework point, she has to do $n\div5$ (rounded up) homework assignments. For example, when she has 11 points, it will take $12\div5=2.4\rightarrow3$ homework assignments to earn her $12^{\text{th}}$ point. What is the smallest number of homework assignments necessary to earn a total of 25 homework points?
        A: Let's think step by step.
        Solution: Noelle only has to do 1 homework assignment to earn her first point,
        and the same is true for each of her first five points.
        She must then do 2 homework assignments to earn her sixth point, seventh point, and so on, up to her tenth point.
        Continuing, we see that Noelle must do a total of \[1+1+1+1+1+2+2+2+2+2+\dots+5+5+5+5+5\] homework assignments to earn 25 points.
        This sum may be rewritten as $5(1+2+3+4+5)=5(15)=\boxed{75}$.
        Final answer: 75

        Question: Sam bought a dozen boxes, each with 30 highlighter pens inside, for $10 each box. He rearranged five of these boxes into packages of six highlighters each and sold them for $3 per package. He sold the rest of the highlighters separately at the rate of three pens for $2. How much profit did he make in total, in dollars?
        A: Let's think step by step.
        Solution: Sam bought 12 boxes x $10 = $120 worth of highlighters.
        He bought 12 * 30 = 360 highlighters in total.
        Sam then took 5 boxes × 6 highlighters/box = 30 highlighters.
        He sold these boxes for 5 * $3 = $15
        After selling these 5 boxes there were 360 - 30 = 330 highlighters remaining.
        These form 330 / 3 = 110 groups of three pens.
        He sold each of these groups for $2 each, so made 110 * 2 = $220 from them.
        In total, then, he earned $220 + $15 = $235.
        Since his original cost was $120, he earned $235 - $120 = $115 in profit.
        Final answer: 115

        Question: The quadratic equation $x^2+mx+n=0$ has roots that are twice those of $x^2+px+m=0,$ and none of $m,$ $n,$ and $p$ is zero. What is the value of $n/p?$
        A: Let's think step by step.
        Solution: Let $r_1$ and $r_2$ be the roots of $x^2+px+m=0.$
        Since the roots of $x^2+mx+n=0$ are $2r_1$ and $2r_2,$ we have the following relationships: \[
        m=r_1 r_2,\quad n=4r_1 r_2,\quad p=-(r_1+r_2), \quad\text{and}\quad
        m=-2(r_1+r_2).
        \] So \[
        n = 4m, \quad p = \frac{1}{2}m,
        \quad\text{and}\quad
        \frac{n}{p}=\frac{4m}{\frac{1}{2}m}=\boxed{8}.
        \]
        Alternatively, the roots of \[
        \left(\frac{x}{2}\right)^2 + p\left(\frac{x}{2}\right) + m = 0
        \] are twice those of $x^2 + px + m = 0.$
        Since the first equation is equivalent to $x^2 + 2px + 4m = 0,$
        we have \[m = 2p \quad\text{and}\quad n = 4m, \quad\text{so}\quad \frac{n}{p} = \boxed{8}.\]
        Final answer: 8

        Question: A group of 4 fruit baskets contains 9 apples, 15 oranges, and 14 bananas in the first three baskets and 2 less of each fruit in the fourth basket. How many fruits are there?
        A: Let's think step by step.
        Solution: For the first three baskets, the number of apples and oranges in one basket is 9+15=24
        In total, together with bananas, the number of fruits in one basket is 24+14=38 for the first three baskets.
        Since there are three baskets each having 38 fruits, there are 3*38=114 fruits in the first three baskets.
        The number of apples in the fourth basket is 9-2=7
        There are also 15-2=13 oranges in the fourth basket
        The combined number of oranges and apples in the fourth basket is 13+7=20
        The fourth basket also contains 14-2=12 bananas.
        In total, the fourth basket has 20+12=32 fruits.
        The four baskets together have 32+114=146 fruits.
        Final answer: 146

        Question: You can buy 4 apples or 1 watermelon for the same price. You bought 36 fruits evenly split between oranges, apples and watermelons, and the price of 1 orange is $0.50. How much does 1 apple cost if your total bill was $66?
        A: Let's think step by step.
        Solution: If 36 fruits were evenly split between 3 types of fruits, then I bought 36/3 = 12 units of each fruit
        If 1 orange costs $0.50 then 12 oranges will cost $0.50 * 12 = $6
        If my total bill was $66 and I spent $6 on oranges then I spent $66 - $6 = $60 on the other 2 fruit types.
        Assuming the price of watermelon is W, and knowing that you can buy 4 apples for the same price and that the price of one apple is A, then 1W=4A
        If we know we bought 12 watermelons and 12 apples for $60, then we know that $60 = 12W + 12A
        Knowing that 1W=4A, then we can convert the above to $60 = 12(4A) + 12A
        $60 = 48A + 12A
        $60 = 60A
        Then we know the price of one apple (A) is $60/60= $1
        Final answer: 1

        Question: Mark's basketball team scores 25 2 pointers, 8 3 pointers and 10 free throws.  Their opponents score double the 2 pointers but half the 3 pointers and free throws.  What's the total number of points scored by both teams added together?
        A: Let's think step by step.
        Solution: Mark's team scores 25 2 pointers, meaning they scored 25*2= 50 points in 2 pointers.
        His team also scores 6 3 pointers, meaning they scored 8*3= 24 points in 3 pointers
        They scored 10 free throws, and free throws count as one point so they scored 10*1=10 points in free throws.
        All together his team scored 50+24+10= 84 points
        Mark's opponents scored double his team's number of 2 pointers, meaning they scored 50*2=100 points in 2 pointers.
        His opponents scored half his team's number of 3 pointers, meaning they scored 24/2= 12 points in 3 pointers.
        They also scored half Mark's team's points in free throws, meaning they scored 10/2=5 points in free throws.
        All together Mark's opponents scored 100+12+5=117 points
        The total score for the game is both team's scores added together, so it is 84+117=201 points
        Final answer: 201

        Question: Bella has two times as many marbles as frisbees. She also has 20 more frisbees than deck cards. If she buys 2/5 times more of each item, what would be the total number of the items she will have if she currently has 60 marbles?
        A: Let's think step by step.
        Solution: When Bella buys 2/5 times more marbles, she'll have increased the number of marbles by 2/5*60 = 24
        The total number of marbles she'll have is 60+24 = 84
        If Bella currently has 60 marbles, and she has two times as many marbles as frisbees, she has 60/2 = 30 frisbees.
        If Bella buys 2/5 times more frisbees, she'll have 2/5*30 = 12 more frisbees.
        The total number of frisbees she'll have will increase to 30+12 = 42
        Bella also has 20 more frisbees than deck cards, meaning she has 30-20 = 10 deck cards
        If she buys 2/5 times more deck cards, she'll have 2/5*10 = 4 more deck cards.
        The total number of deck cards she'll have is 10+4 = 14
        Together, Bella will have a total of 14+42+84 = 140 items
        Final answer: 140

        Question: In a certain school, 2/3 of the male students like to play basketball, but only 1/5 of the female students like to play basketball. What percent of the population of the school do not like to play basketball if the ratio of the male to female students is 3:2 and there are 1000 students?
        A: Let's think step by step.
        Solution: The students are divided into 3 + 2 = 5 parts where 3 parts are for males and 2 parts are for females.
        Each part represents 1000/5 = 200 students.
        So, there are 3 x 200 = 600 males.
        And there are 2 x 200 = 400 females.
        Hence, 600 x 2/3 = 400 males play basketball.
        And 400 x 1/5 = 80 females play basketball.
        A total of 400 + 80 = 480 students play basketball.
        Therefore, 1000 - 480 = 520 do not like to play basketball.
        The percentage of the school that do not like to play basketball is 520/1000 * 100 = 52
        Final answer: 52
        
        Question: Kevin Kangaroo begins hopping on a number line at 0. He wants to get to 1, but he can hop only $\frac{1}{3}$ of the distance. Each hop tires him out so that he continues to hop $\frac{1}{3}$ of the remaining distance. How far has he hopped after five hops? Express your answer as a common fraction.
        A: Let's think step by step.
        Solution: Kevin hops $1/3$ of the remaining distance with every hop.
        His first hop takes $1/3$ closer.
        For his second hop, he has $2/3$ left to travel, so he hops forward $(2/3)(1/3)$.
        For his third hop, he has $(2/3)^2$ left to travel, so he hops forward $(2/3)^2(1/3)$.
        In general, Kevin hops forward $(2/3)^{k-1}(1/3)$ on his $k$th hop.
        We want to find how far he has hopped after five hops.
        This is a finite geometric series with first term $1/3$, common ratio $2/3$, and five terms.
        Thus, Kevin has hopped $\frac{\frac{1}{3}\left(1-\left(\frac{2}{3}\right)^5\right)}{1-\frac{2}{3}} = \boxed{\frac{211}{243}}$.
        Final answer: \frac{211}{243}}

        Question: What is the area of the region defined by the equation $x^2+y^2 - 7 = 4y-14x+3$?
        A: Let's think step by step.
        Solution: We rewrite the equation as $x^2 + 14x + y^2 - 4y = 10$ and then complete the square,
        resulting in  $(x+7)^2-49 + (y-2)^2-4=10$,
        or $(x+7)^2+(y-2)^2=63$.
        This is the equation of a circle with center $(-7, 2)$ and radius $\sqrt{63},$
        so the area of this region is $\pi r^2 = \boxed{63\pi}$.
        Final answer: 63\pi

        Question: Expand $(2z^2 + 5z - 6)(3z^3 - 2z + 1)$.
        A: Let's think step by step.
        Solution: $$\begin{array}{crrrrrrr}
        & & & 3z^3 & & -2z & + 1 & \\
        \times & & & & 2z^2 & +5z & -6 \\
        \cline{1-7}\rule{0pt}{0.17in}
        & & & -18z^3 & & +12z & -6 & \\
        & & +15z^4 & & -10z^2 & +5z & & \\
        + & 6z^5 & & -4z^3 & +2z^2 & & & \\
        \cline{1-7}\rule{0pt}{0.17in}
        & 6z^5 & +15z^4 & -22z^3 & - 8z^2 &+17z & -6 &
        \end{array}$$
        Final answer: 6z^5+15z^4-22z^3-8z^2+17z-6}

        Question: If $x^2+y^2=1$, what is the largest possible value of $|x|+|y|$?
        A: Let's think step by step.
        Solution: If $(x,y)$ lies on the circle,
        so does $(x,-y),$ $(-x,-y),$ and $(-x,-y),$ (which all give the same value of $|x| + |y|$),
        so we can assume that $x \ge 0$ and $y \ge 0.$
        Then $|x| + |y| = x + y.$  Squaring, we get
        \[(x + y)^2 = x^2 + 2xy + y^2 = 1 + 2xy.\]
        Note that $(x - y)^2 \ge 0.$
        Expanding, we get $x^2 - 2xy + y^2 \ge 0,$ so $2xy \le x^2 + y^2 = 1.$
        Hence,\[1 + 2xy \le 2,\]which means $x + y \le \sqrt{2}.$
        Equality occurs when $x = y = \frac{1}{\sqrt{2}},$
        so the maximum value of $|x| + |y|$ is $\boxed{\sqrt{2}}.$
        Final answer: \sqrt{2}

        Question: If $f(x)=\frac{ax+b}{cx+d}, abcd\not=0$ and $f(f(x))=x$ for all $x$ in the domain of $f$, what is the value of $a+d$?
        A: Let's think step by step.
        Solution: The condition $f(f(x))$ means that $f$ is the inverse of itself,
        so its graph is symmetrical about the line $y = x$.
        With a rational function of this form, we will have two asymptotes:
        a vertical one at $x=-d/c$ if $cx+d$ does not divide $ax+b$,
        and a horizontal one at $y=a/c$,
        if we take the limit of $f(x)$ as $x$ goes to $\pm\infty$.
        In order for $f$ to be its own inverse, the intersection of the asymptotes must lie on the line $y=x$
        so that it and its asymptotes reflect onto themselves.
        This means that $-d/c=a/c$,
        and therefore $-d=a$ and $a+d=\boxed{0}$.
        Final answer: 0
        """

        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {dataset_row[self.config.rephrased_question_column]} \n A: Let's think step by step.",
            },
        ]

    def parse(self, dataset_row: dict, response: Answer):
        """
        Parse the response from the completions model and keep
        predicted answers that match the ground truth rephrased
        answer.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            A list of dictionaries with the original question, answer, and the rephrased question and answer.
        """
        cleaned_predicted_answer = str(response.final_answer).replace("$", "")
        cleaned_ground_truth_answer = dataset_row[self.config.answer_column].replace(
            "$", ""
        )
        if cleaned_predicted_answer == cleaned_ground_truth_answer:
            dataset_row[self.config.output_predicted_answer_column] = response.solution
            return [dataset_row]
        return []
