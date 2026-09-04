# Step 1: Generate Topics (25)

        role_name="Assistant",
       content="You are a helpful assistant.",
        role_name="User",
        content=prompt,

    GENERATE_TOPICS = TextPrompt(
        """Please list {num_topics} diverse math topics. Make sure the topics are math topics. No explanation. Respond in json format: 
{{ "topics": list[str] }}
"""
    )

# Step 2: Generate tasks (subtopics) (25 for each topic)


        role_name="Assistant",
        content="You are a helpful assistant.",
        role_name="User",
    GENERATE_TASKS = TextPrompt(
        """List {num_tasks} different math {topic} problem topics. Be precise and make sure the problems are {topic} problems. Respond in json format: 
{{ "subtopics": list[str] }}
"""
    )


# Step 3: Generate questions (80 for math, 32 for chemistry, 32 for biology, for each task)
        role_name="Assistant",
        content="You are a Biologist.", / Physicist / Mathematician

        TASK_SPECIFY_PROMPT = TextPrompt(
                """From this {discipline} subject {topic} and this subtopic {task} we need to write a new questions for a {discipline} student to solve.
        Please write a precise problem for the student to solve. Respond in json format: 
        "problem": str
        """
        )

# Step 4: Generate answers (for each question)

    discipline_expert = "Mathematician" / "Physicist" / "Biologist"
    SOLUTION_GENERATION_PROMPT = TextPrompt("""You are a {discipline_expert}, solve the following question: {question}.""")
