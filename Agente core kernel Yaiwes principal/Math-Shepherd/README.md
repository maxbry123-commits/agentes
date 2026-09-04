---
tags:
- prm
- synthesized data
---
# Dataset Card for Math-Shepherd
Project Page: [Math-Shepherd](https://rain-motion-6ec.notion.site/Math-Shepherd-A-Label-Free-Step-by-Step-Verifier-for-LLMs-in-Mathematical-Reasoning-41b6e73c860840e08697d347f8889bac#08e86c6d44c4452ba0b78c7aaea5f4f7)

Paper: https://arxiv.org/pdf/2312.08935.pdf

# Data Loading
```
from datasets import load_dataset
dataset = load_dataset("peiyi9979/Math-Shepherd")
```

# Data Instance
Every instance consists of three data fields: "input," "label," and "task".

1. "input": problem + step-by-step solution, e.g.,
```
If Buzz bought a pizza with 78 slices at a restaurant and then decided to share it with the waiter in the ratio of 5:8, with Buzz's ratio being 5, what's twenty less the number of slices of pizza that the waiter ate? 

Step 1: The total ratio representing the pizza is 5+8 = <<5+8=13>>13. ки

Step 2: The waiter ate 13 x 8 / 13 = <<13*8/13=6>>6 slices of the pizza. ки

Step 3: Buzz ate 78 - 6 = <<78-6=72>>72 slices of the pizza. ки

Step 4: The waiter ate 20 less than the number of slices that Buzz ate which is 72 - 20 = 52. ки

Step 5: The waiter ate 52 slices of the pizza. The answer is: 52 ки
```

2. "label": problem + step-by-step solution with automatic label, e.g.,
```
If Buzz bought a pizza with 78 slices at a restaurant and then decided to share it with the waiter in the ratio of 5:8, with Buzz's ratio being 5, what's twenty less the number of slices of pizza that the waiter ate? 

Step 1: The total ratio representing the pizza is 5+8 = <<5+8=13>>13. + 

Step 2: The waiter ate 13 x 8 / 13 = <<13*8/13=6>>6 slices of the pizza. - 

Step 3: Buzz ate 78 - 6 = <<78-6=72>>72 slices of the pizza. - 

Step 4: The waiter ate 20 less than the number of slices that Buzz ate which is 72 - 20 = 52. - 

Step 5: The waiter ate 52 slices of the pizza. The answer is: 52 -
```

3. "task": `GSM8K` or `MATH`.

NOTE:

"`ки`" serves as a unique token denoting the position for predicting the step score.

"`+`" signifies a good step, as it has the potential to lead towards the correct answer.

"`-`" denotes a bad step.

When we train PRMs, we only compute the loss of the positions of `ки`.

# Models:
We utilized internal code for step-wise PPO training, which cannot be open-sourced. We hope for your understanding. We provide the checkpoints of SFT, PRM, and RL models to help everyone reproduce our results.

- Mistral-7b-sft: https://huggingface.co/peiyi9979/mistral-7b-sft
- Mistral-7b-prm: https://huggingface.co/peiyi9979/math-shepherd-mistral-7b-prm
- Mistral-7b-rl:  https://huggingface.co/peiyi9979/math-shepherd-mistral-7b-rl