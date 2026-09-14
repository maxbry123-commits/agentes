from pocketflow import Node, Flow
import nodes_dom
import nodes_vision


def _build_loop(nodes):
    """Wire an Observe -> Decide -> Act loop from a nodes module.

    The flow works like this:
    1. Observe reads the page (as text elements, or as a screenshot)
    2. Decide makes one LLM call and picks the next action (or "done")
    3. If there's an action, Act performs it, then we loop back to Observe
    4. If Decide says "done", we stop
    """
    observe, decide, act = nodes.Observe(), nodes.Decide(max_retries=3), nodes.Act()
    finish = Node()  # a bare Node with no successors: the loop's exit door

    observe - "decide" >> decide   # after looking, think
    decide - "act" >> act          # if there's an action, do it
    decide - "done" >> finish      # if the goal is met, stop
    act - "observe" >> observe     # after acting, look again

    return Flow(start=observe)


def create_dom_agent_flow():
    """Browser agent that reads the DOM as a numbered list and clicks by element number."""
    return _build_loop(nodes_dom)


def create_vision_agent_flow():
    """Browser agent that reads a screenshot and clicks by x/y pixel coordinates."""
    return _build_loop(nodes_vision)
