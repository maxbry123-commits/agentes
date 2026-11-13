"""Prompts for answer generation and LLM-judge scoring."""

QA_GENERATION_PROMPT = """You are a helpful assistant answering questions based on the provided context.

Context:
{context}

Question: {question}

Instructions:
1. Answer the question using the provided context. Be specific and cite concrete details from the context.
2. For time-related questions, follow these steps:
   Step 1: Find the conversation date from the header (e.g., [1:56 pm on 8 May, 2023] means the conversation date is 8 May 2023).
   Step 2: Identify the relative time expression (e.g., "yesterday", "last week", "last Saturday").
   Step 3: Calculate the actual date. "yesterday" = conversation date minus 1 day. "last week" = approximately 7 days before. "last Saturday" = the most recent Saturday before the conversation date. "next month" = the month after the conversation month.
   Step 4: State the calculated date in your answer.
3. When multiple events of the same type exist (e.g., multiple camping trips, multiple beach visits), distinguish between them using their dates.
4. Prefer quoting specific details (names, dates, objects, places) from the context over paraphrasing.
5. If the context contains partial but relevant information, provide the best answer you can.
6. Only say you cannot answer if the context truly contains NO relevant information at all.

Answer:"""


LLM_JUDGE_PROMPT = """You are an evaluation judge. Compare the generated answer with the gold answer and determine if the generated answer is correct.

Be lenient with format differences. For example:
- "May 7th" and "7 May" are the same date -> CORRECT
- "Caesar salad" and "She ordered a Caesar salad" -> CORRECT (same meaning)
- Partial but accurate answers are CORRECT

Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

First, provide a short (one sentence) explanation of your reasoning, then finish with CORRECT or WRONG.

Return your response in JSON format:
{{"reasoning": "your explanation", "label": "CORRECT or WRONG"}}"""

