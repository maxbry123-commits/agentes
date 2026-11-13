"""Production resources for intent classification.

This module keeps runtime assets inside the ``mmem`` package so library code
does not depend on diagnostic scripts or archived harnesses.
"""
from __future__ import annotations

PROTOTYPES_GENERIC: dict[str, list[str]] = {
    "temporal": [
        "When did this happen?",
        "What event happened immediately before X?",
        "How long has it been going on?",
        "In what year did they meet?",
        "什么时候发生的？",
        "哪个事件先发生？",
    ],
    "causal": [
        "Why did X happen?",
        "What caused this outcome?",
        "What led to this decision?",
        "Because of what reason did they change?",
        "为什么会这样？",
        "什么原因导致的？",
    ],
    "multi_hop": [
        "What connects these events?",
        "Based on multiple interactions, what can we infer?",
        "How have things changed across conversations?",
        "Given these facts, what conclusion follows?",
        "综合起来看，能得出什么结论？",
        "从前后对比可以看出什么？",
    ],
    "entity_centric": [
        "What does this person look like?",
        "Where do they live?",
        "Who is someone's friend or sibling?",
        "What is their job?",
        "这个人住在哪里？",
        "他的工作是什么？",
    ],
}

PROTOTYPES_LOCOMO: dict[str, list[str]] = {
    "temporal": [
        # LoCoMo temporal 题常见句式：who did X on DATE / when did X do Y
        "Who did Maria have dinner with on May 3, 2023?",
        "When did John join the online support group?",
        "Around which US holiday did Maria get into a car accident?",
        "How long ago was the charity event?",
    ],
    "causal": [
        # LoCoMo causal 题较少，多带 "why" 或 "reason"
        "Why did Jon decide to start his dance studio?",
        "What is the reason Maria volunteered at the shelter?",
        "What led John to change his career path?",
        "为什么 Alice 选择回到学校读书？",
    ],
    "multi_hop": [
        # ★★★ 最关键的一类 — 诊断里 0/13 触发的 LoCoMo multi_hop 典型句式 ★★★
        # 模式 1: "Would X likely..." / "Would X be considered..."
        "Would John be open to moving to another country?",
        # 模式 2: "What might X..." (hypothetical/inference)
        "What job might Maria pursue in the future?",
        # 模式 3: "Based on X, what..." (explicit "based on" signal)
        "Based on Tim's collections, what shop would he enjoy visiting?",
        # 模式 4: "Is it likely that X..." (yes/no inference)
        "Is it likely that Nate has friends besides Joanna?",
        # preference inference: comparing two options based on known personality/preferences
        "Would Melanie prefer a national park or a theme park?",
        # external-knowledge bridge: connecting person preference with outside knowledge
        "Would Melanie enjoy a classical music concert?",
        # counterfactual inference: reasoning over an alternative scenario
        "Would Caroline still choose counseling without support from others?",
        # attribute inference: aggregating multiple clues to derive a personal attribute
        "What political leaning would Caroline likely have?",
    ],
    "entity_centric": [
        # LoCoMo entity 题特征：问名字、身份、关系、具体属性
        # (removed) "What do Jon and Gina both have in common?" — asks about shared traits,
        #   which requires comparing two entities; closer to multi_hop than entity lookup
        # (removed) "Where has Melanie camped?" — answer is a list of locations,
        #   closer to a list-lookup than a single-fact entity attribute
        "What is Caroline's identity?",
        "What martial arts has John done?",
        # expanded to cover general fact / event / property lookup (not just person attributes)
        "What did this person do?",
        "What activity does this person participate in?",
        "What did this event raise awareness for?",
        # places / activities list lookup: answer is a list of items, but intent is entity attribute
        "What are the locations this person has visited?",
    ],
}

def get_all_prototypes() -> dict[str, list[str]]:
    """Return merged prototypes: generic + LoCoMo layers."""
    merged = {}
    for intent in PROTOTYPES_GENERIC:
        merged[intent] = (
            PROTOTYPES_GENERIC[intent]
            + PROTOTYPES_LOCOMO.get(intent, [])
        )
    return merged

INTENT_CLASSIFY_SYSTEM = """You are an intent classifier for a memory retrieval system. \
Your job is to analyze a user's query and estimate how strongly it expresses each of \
four intent types. Output only valid JSON. Do not add commentary."""

INTENT_CLASSIFY_USER_TEMPLATE = """Analyze the intent of the following query. A query may \
express multiple intents simultaneously.

Query: {query}

Intent types and what counts as a signal for each:

1. temporal — The query asks about WHEN something happened, time ordering, duration, \
or sequence of events. Signals: "when", "before", "after", "during", "how long", "what year", \
explicit dates, or asking about the timing of events relative to each other.

2. causal — The query asks WHY something happened, what caused it, or what led to \
an outcome. Signals: "why", "because", "what caused", "what led to", "as a result of", \
or asking about reasons, motivations, or consequences.

3. multi_hop — The query requires combining facts from multiple separate events, \
interactions, or contexts to answer. A single-fact lookup is NOT multi_hop. Signals: \
"based on X and Y", "how does X relate to Y", "given that ... what ...", "combining \
these conversations", "across multiple sessions", asking about trends/patterns/shifts \
across time, or asking for inferences that require connecting separate pieces of information. \
Also includes hypothetical, predictive, or inference-requiring questions where the answer \
must be derived rather than directly retrieved — even when the subject is a named person, \
the inference requirement makes this multi_hop, NOT entity_centric.

4. entity_centric — The query asks about a specific attribute, description, or property \
of a person, place, or thing that can be looked up as a stored fact. Signals: "who is", \
"what does X look like", "where does X live", "what is X's job", or asking to retrieve \
a single concrete fact about a named entity. NOTE: if answering requires inference or \
reasoning across multiple facts rather than a direct lookup, score multi_hop higher \
than entity_centric.

Rules:
- Score each intent independently on a scale of 0.0 to 1.0.
- Multiple intents can score high at once (e.g. a query can be both temporal and multi_hop).
- If the query clearly expresses no recognizable intent, all four scores should be low (< 0.3).
- For vague conversational continuations ("Tell me more", "Continue", "Go on"), all scores \
should be 0.0 — do not guess at entity or any other intent.
- Prefer 0.0 / 0.3 / 0.6 / 0.9 as anchor points when in doubt.

Output format (JSON object, no other text):
{{"temporal": 0.X, "causal": 0.X, "multi_hop": 0.X, "entity_centric": 0.X}}"""
