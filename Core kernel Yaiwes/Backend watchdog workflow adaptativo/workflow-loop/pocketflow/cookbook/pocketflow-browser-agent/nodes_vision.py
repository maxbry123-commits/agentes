"""Vision mode: the agent looks at a SCREENSHOT and clicks by x/y COORDINATES.

Only Observe and Act differ from DOM mode. This is what Operator / Claude computer
use / Gemini do: universal (if a human can see it, the model can), but the model
has to *guess* where to click — the grounding problem — so it's slower and pricier.
"""
from pocketflow import Node
from utils import call_llm, parse_yaml

MAX_STEPS = 12          # safety cap so a confused agent can't loop forever
WIDTH, HEIGHT = 1280, 720  # viewport the coordinates are scaled to


class Observe(Node):
    """Grab a screenshot of the current page."""

    def prep(self, shared):
        return shared["page"]

    def exec(self, page):
        return page.screenshot()

    def post(self, shared, prep_res, shot):
        shared["shot"] = shot
        print("📸 Took a screenshot")
        return "decide"


class Decide(Node):
    """One vision-LLM call: look at the screenshot and pick the next action + coords."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        prompt = f"""You are a computer-use agent looking at a screenshot of a web page.
Work toward this goal, ONE action at a time.

GOAL: {shared['goal']}

Actions already taken:
{chr(10).join(shared['history']) or '(none)'}

Coordinates are x, y integers from 0 to 999 (top-left is 0,0), scaled to the image.
To fill a text field: first click it, then type. To use a dropdown: click it, then
press its option keys (e.g. key: ArrowDown, key: Enter).

Reply with ONLY a yaml block:
```yaml
thinking: "<one short sentence>"
action: click | type | key | done
x: <0-999, for click>
y: <0-999, for click>
text: "<text to type, for type>"
key: "<key name, for key>"
answer: "<final answer in double quotes, only if action is done>"
```"""
        return parse_yaml(call_llm(prompt, image=shared["shot"]))

    def post(self, shared, prep_res, decision):
        shared["decision"] = decision
        print(f"🤔 {decision.get('thinking', '')}")
        if decision["action"] == "done" or len(shared["history"]) >= MAX_STEPS:
            shared["answer"] = decision.get("answer", "")
            return "done"
        return "act"


class Act(Node):
    """Carry out the action at the raw pixel coordinates the model guessed."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        d, page = shared["decision"], shared["page"]
        if d["action"] == "click":
            page.mouse.click(d["x"] / 1000 * WIDTH, d["y"] / 1000 * HEIGHT)
            note = f'click ({d["x"]}, {d["y"]})'
        elif d["action"] == "type":
            page.keyboard.type(str(d["text"]))
            note = f'type "{d["text"]}"'
        elif d["action"] == "key":
            page.keyboard.press(str(d["key"]))
            note = f'key {d["key"]}'
        page.wait_for_timeout(300)  # let the page react
        return note

    def post(self, shared, prep_res, note):
        shared["history"].append(note)
        print(f'🖐️  step {len(shared["history"])} | {note}')
        return "observe"  # back to the top of the loop
