import os
import sys
import time
from playwright.sync_api import sync_playwright
from flow import create_dom_agent_flow, create_vision_agent_flow

# By default the agent drives a tiny local "Pocket Cafe" page bundled with this
# cookbook, so it runs the same way every time with no external site required.
DEFAULT_SITE = "file://" + os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "demo_site", "index.html"
)
DEFAULT_GOAL = "Order a large Latte for Sam, then report the confirmation message."


def main():
    """Drive a real browser toward a goal, one Observe -> Decide -> Act step at a time."""
    url, goal, mode, headless = DEFAULT_SITE, DEFAULT_GOAL, "dom", False

    # Options: --mode=dom|pixels --url=<page> --goal=<goal> --headless
    for arg in sys.argv[1:]:
        if arg.startswith("--mode="):
            mode = arg[len("--mode="):]
        elif arg.startswith("--url="):
            url = arg[len("--url="):]
        elif arg.startswith("--goal="):
            goal = arg[len("--goal="):]
        elif arg == "--headless":
            headless = True

    if mode == "pixels":
        agent_flow = create_vision_agent_flow()   # sees a screenshot, clicks coordinates
    else:
        agent_flow = create_dom_agent_flow()       # reads the DOM, clicks by element number

    print(f"🌐 Site: {url}")
    print(f"🎯 Goal: {goal}")
    print(f"👁️  Mode: {mode} ({'screenshots + coordinates' if mode == 'pixels' else 'DOM text + element numbers'})\n")

    with sync_playwright() as p:
        # A fixed viewport so pixel-mode coordinates line up with what the model sees.
        page = p.chromium.launch(headless=headless).new_page(
            viewport={"width": 1280, "height": 720}
        )
        page.goto(url)

        shared = {"page": page, "goal": goal, "history": []}
        start = time.time()
        agent_flow.run(shared)

        print(f"\n✅ Finished in {len(shared['history'])} actions, {time.time() - start:.1f}s")
        print(f"📋 Answer: {shared.get('answer', '')}")


if __name__ == "__main__":
    main()
