"""DOM mode: the agent reads the page's structured elements as text.

It never looks at pixels — it asks the browser for its list of interactive
elements, numbers them, and clicks by element number. Cheap, precise, fast,
but blind to anything not in the DOM (canvas, native apps, some PDFs).
"""
from pocketflow import Node
from utils import call_llm, parse_yaml

MAX_STEPS = 12  # safety cap so a confused agent can't loop forever


class Observe(Node):
    """Read the live page into a compact, numbered list of interactive elements."""

    def prep(self, shared):
        return shared["page"]

    def exec(self, page):
        # Ask the browser for every clickable / typable element and number them.
        els, lines = [], []
        for el in page.query_selector_all("a, button, input, select, textarea"):
            if not el.is_visible():
                continue
            tag = el.evaluate("e => e.tagName.toLowerCase()")
            label = (el.get_attribute("aria-label") or el.get_attribute("placeholder")
                     or ("" if tag == "select" else el.inner_text()) or "").strip()[:60]
            extra = ""
            if tag in ("input", "textarea"):
                extra = f' value="{el.input_value()}"'
            if tag == "select":
                options = [o.inner_text() for o in el.query_selector_all("option")]
                extra = f' value="{el.input_value()}" options={options}'
            if el.is_disabled():
                extra += " (disabled)"
            lines.append(f'[{len(els)}] <{tag}> "{label}"{extra}')
            els.append(el)  # els[i] is the live handle for the line printed as [i]
        text = page.evaluate("() => document.body.innerText")[:1000]
        return els, lines, page.title(), text

    def post(self, shared, prep_res, exec_res):
        shared["els"], shared["lines"], shared["title"], shared["text"] = exec_res
        print(f"👀 Observed {len(shared['els'])} elements on \"{shared['title']}\"")
        return "decide"


class Decide(Node):
    """One LLM call: given the element list and the goal, pick the next action."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        prompt = f"""You are a browser agent. Work toward this goal, ONE action at a time.

GOAL: {shared['goal']}

Current page: "{shared['title']}"
Interactive elements:
{chr(10).join(shared['lines'])}

Visible page text:
{shared['text']}

Actions already taken:
{chr(10).join(shared['history']) or '(none)'}

Reply with ONLY a yaml block:
```yaml
thinking: "<one short sentence>"
action: click | type | select | press | done
target: <element number, omit if done or press>
text: "<text to type, option to select, or key to press (e.g. Enter); omit otherwise>"
answer: "<final answer in double quotes, only if action is done>"
```"""
        return parse_yaml(call_llm(prompt))

    def post(self, shared, prep_res, decision):
        shared["decision"] = decision
        print(f"🤔 {decision.get('thinking', '')}")
        if decision["action"] == "done" or len(shared["history"]) >= MAX_STEPS:
            shared["answer"] = decision.get("answer", "")
            return "done"
        return "act"


class Act(Node):
    """Carry out the one action Decide chose, by element number, via Playwright."""

    def prep(self, shared):
        return shared

    def exec(self, shared):
        d = shared["decision"]
        if d["action"] == "press":
            shared["page"].keyboard.press(str(d["text"]))
            shared["page"].wait_for_timeout(1000)
            return f'press {d["text"]}'
        el = shared["els"][d["target"]]  # look up the live handle by its number
        if d["action"] == "click":
            el.click()
        elif d["action"] == "type":
            el.fill(str(d["text"]))
        elif d["action"] == "select":
            el.select_option(label=str(d["text"]))
        shared["page"].wait_for_timeout(300)  # let the page react
        return f'{d["action"]} {shared["lines"][d["target"]]} {d.get("text", "")}'.strip()

    def post(self, shared, prep_res, note):
        shared["history"].append(note)
        print(f'🖐️  step {len(shared["history"])} | {note}')
        return "observe"  # back to the top of the loop
