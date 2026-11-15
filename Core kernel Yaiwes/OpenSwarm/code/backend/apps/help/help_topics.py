"""Curated product knowledge for the in-app help chat.

Every fact here is written from the CODE, not from the docs site, and ships inside the same
build as the surfaces it describes, so help can never describe a version the user isn't running.
Each topic is self-contained on purpose: the help panel searches these offline with no model at
all, and the chat gets them as a cached system-prompt block.

When you move or rename a surface, update the topic in the SAME change. A help topic that lies is
worse than no help topic.
"""

from typing import List

from pydantic import BaseModel, ConfigDict


class HelpTopic(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: str
    title: str
    # Where the thing physically is on screen. Empty when the topic is a concept, not a surface.
    where: str
    body: str
    keywords: List[str]


HELP_TOPICS: List[HelpTopic] = [
    HelpTopic(
        id="canvas",
        title="The dashboard canvas",
        where="The whole main window.",
        body=(
            "Each dashboard is an infinite canvas holding cards: agent chats, browsers, apps you "
            "built, and workflows. Scroll or pinch to zoom, hold Space and drag to pan, drag a card "
            "by its header to move it, and drag on empty canvas to marquee-select several."
        ),
        keywords=["canvas", "dashboard", "zoom", "pan", "move", "cards", "select"],
    ),
    HelpTopic(
        id="dock",
        title="The dock",
        where="A dark vertical rail down the left edge of the window.",
        body=(
            "Every open card gets a colored tile at the top of the dock; click one to jump to that "
            "card, right-click it for its menu. Below the divider sit four actions in this order: "
            "New browser, Workflows, then Settings and Applications."
        ),
        keywords=["dock", "rail", "sidebar", "left", "tiles", "icons"],
    ),
    HelpTopic(
        id="applications",
        title="Applications, your app library",
        where="The grid icon at the very bottom of the left dock.",
        body=(
            "Opens a window listing every app you have built or imported, with thumbnails. Click one "
            "to drop it onto the current dashboard as a live card. A search box appears once you have "
            "more than eight apps. It lists YOUR apps, not the programs installed on your computer."
        ),
        keywords=["applications", "apps", "library", "grid", "built", "outputs"],
    ),
    HelpTopic(
        id="new-chat",
        title="Starting a new chat",
        where="The 'Ask me anything...' pill at the bottom center of the canvas.",
        body=(
            "Type in the pill and press Enter to spawn an agent card. The pill is hidden while a "
            "dashboard is completely empty, so the keyboard shortcut is the reliable way in; it works "
            "from anywhere. The new card lands beside whatever is selected, otherwise in view."
        ),
        keywords=["new chat", "agent", "spawn", "pill", "ask", "start", "composer"],
    ),
    HelpTopic(
        id="window-controls",
        title="Card window controls and tiling",
        where="The three traffic-light dots in the top-left corner of any card.",
        body=(
            "Red closes, yellow minimizes, green toggles full screen. HOVER the green dot instead of "
            "clicking it and a macOS-style tiling menu opens with two groups: Fill and Halves (fill, "
            "left, right, top, bottom) and Quarters. Clicking green again restores a tiled card."
        ),
        keywords=["traffic lights", "fullscreen", "tile", "halves", "quarters", "minimize", "close", "green"],
    ),
    HelpTopic(
        id="minimized",
        title="Minimized cards",
        where="A stack of small thumbnails on the right edge of the canvas.",
        body=(
            "Minimizing a card with the yellow dot parks it in the right-edge stack instead of closing "
            "it. Click a thumbnail to put the card back on the canvas exactly where it was."
        ),
        keywords=["minimize", "minimized", "restore", "stack", "thumbnail", "yellow"],
    ),
    HelpTopic(
        id="spaces",
        title="Dashboards, which behave like Spaces",
        where="Rest the cursor on the very top edge of the window to reveal the spaces bar.",
        body=(
            "Dashboards are separate canvases, like macOS Spaces. The top-edge bar switches between "
            "them, + adds one, and right-clicking a space renames or removes it. There is also a "
            "keyboard shortcut for the previous and next dashboard."
        ),
        keywords=["spaces", "dashboards", "switch", "top edge", "workspace", "add"],
    ),
    HelpTopic(
        id="history",
        title="Chat history",
        where="The island at the top center of the dashboard.",
        body=(
            "History lists past chats across ALL dashboards, not just the current one. Picking a chat "
            "reopens it as a card. It is on the top island, not in the dock."
        ),
        keywords=["history", "past chats", "previous", "reopen", "recent", "island"],
    ),
    HelpTopic(
        id="search",
        title="Search everything",
        where="The global search palette, opened with the search shortcut.",
        body=(
            "One palette searches chats, apps, and commands across every dashboard. There is a "
            "separate find that searches only the cards on the current canvas, and inside a browser "
            "card that same find searches the web page instead."
        ),
        keywords=["search", "find", "palette", "command", "lookup", "cmd k"],
    ),
    HelpTopic(
        id="workflows",
        title="Workflows and scheduled tasks",
        where="The repeating-calendar icon in the left dock, above Settings.",
        body=(
            "A workflow is a sequence of agent steps that runs on a schedule, for example every "
            "weekday at 9am. Open the Workflows window from the dock to create one, set its steps and "
            "schedule, run it immediately with Run now, or pause it. You can also just ask an agent in "
            "chat to schedule something and it will build the workflow for you."
        ),
        keywords=["workflow", "schedule", "scheduled", "task", "cron", "recurring", "automation", "daily"],
    ),
    HelpTopic(
        id="apps",
        title="Building apps",
        where="Ask any agent chat, or the + menu on the canvas.",
        body=(
            "Ask an agent for a tool, dashboard, or game and it calls CreateApp, which seeds a "
            "workspace and puts a live preview card on the dashboard, then writes the code. To change "
            "an app, select its card and tell the agent what to change; the preview reloads itself."
        ),
        keywords=["app", "build", "create", "app builder", "preview", "vite", "code"],
    ),
    HelpTopic(
        id="publish",
        title="Publishing an app to the web",
        where="The share or publish control on a built app's card.",
        body=(
            "An app can be published to a public {slug}.openswarm.host URL. Publishing first scans the "
            "code for anything sensitive and shows the findings before it uploads. Published apps can "
            "be unpublished again from the same place."
        ),
        keywords=["publish", "share", "host", "openswarm.host", "deploy", "public", "link"],
    ),
    HelpTopic(
        id="browser",
        title="Browser cards",
        where="The globe icon in the left dock.",
        body=(
            "A browser card is a real browser on the canvas, with tabs, its own zoom, find-in-page, and "
            "a persistent login session that survives quitting the app. Agents can drive these cards "
            "for you, and you stay signed in to the sites you use."
        ),
        keywords=["browser", "web", "tabs", "globe", "login", "website", "internet"],
    ),
    HelpTopic(
        id="browser-agent",
        title="Agents that use the browser",
        where="Happens automatically inside a chat.",
        body=(
            "When a task needs a real website, the agent delegates to a browser sub-agent, which opens "
            "a browser card and works in it while you watch. It is the last resort: agents prefer "
            "connected tools and plain web search first, because those are faster and more reliable."
        ),
        keywords=["browser agent", "sub-agent", "automation", "click", "website", "delegate"],
    ),
    HelpTopic(
        id="tools",
        title="Tools and MCP integrations",
        where="Settings, then Tools.",
        body=(
            "Integrations (Gmail, Notion, Slack and so on) are MCP servers. They are deliberately NOT "
            "active by default: an agent has to find one with MCPSearch and then activate it with "
            "MCPActivate, which asks for your approval first. Nothing gets tool access silently."
        ),
        keywords=["tools", "mcp", "integration", "connect", "gmail", "notion", "slack", "approval", "activate"],
    ),
    HelpTopic(
        id="approvals",
        title="Approvals",
        where="In the chat card, as a prompt from the agent.",
        body=(
            "Before an agent does something that needs your say-so it stops and asks in the chat. You "
            "approve or deny, and you can tell it to remember the choice so it stops asking for that "
            "same action."
        ),
        keywords=["approval", "permission", "approve", "deny", "hitl", "ask", "confirm"],
    ),
    HelpTopic(
        id="skills",
        title="Skills",
        where="Settings, then Skills.",
        body=(
            "A skill is a reusable set of instructions that teaches agents how to do a specific task. "
            "You can write one, install one from the registry, or import one, and agents pull in a "
            "skill on demand when it is relevant instead of carrying all of them every turn."
        ),
        keywords=["skill", "skills", "instructions", "registry", "teach", "import"],
    ),
    HelpTopic(
        id="dictation",
        title="Voice dictation",
        where="The mic button on the composer, or the dictation shortcut.",
        body=(
            "Dictation transcribes speech locally on your machine and drops the words wherever your "
            "cursor is. The first use downloads a voice model, so it is slower once and fast after. "
            "Hold-to-talk versus click-to-toggle is a setting under General."
        ),
        keywords=["dictation", "voice", "mic", "speak", "transcribe", "talk", "whisper"],
    ),
    HelpTopic(
        id="models",
        title="Connecting a model",
        where="Settings, then Models.",
        body=(
            "You can connect a Claude, ChatGPT, or Gemini subscription, paste an API key, or use "
            "OpenSwarm's own paid plan. Brand-new installs get a small free trial that runs on a "
            "shared pool. If a connection dies, this is the page with the Reconnect button."
        ),
        keywords=["model", "models", "connect", "api key", "subscription", "claude", "gpt", "gemini", "provider", "reconnect", "free trial"],
    ),
    HelpTopic(
        id="settings",
        title="Settings",
        where="The gear icon in the left dock; it opens as a card on the canvas.",
        body=(
            "Sections are Account; then App: General, Appearance, Privacy, Advanced; then "
            "Capabilities: Models, Skills, Tools, Commands, Usage. Theme, accent color, and text size "
            "live under Appearance. Agent defaults and shortcuts live under General."
        ),
        keywords=["settings", "preferences", "gear", "config", "theme", "account", "appearance", "privacy", "advanced", "usage"],
    ),
    HelpTopic(
        id="swarm-file",
        title="Sharing with .swarm files",
        where="Share on the thing you want to export; drag a .swarm file onto the app to import.",
        body=(
            "Apps, skills, and workflows export to a single .swarm file you can send someone. Importing "
            "one adds it to your library. The export is scanned so credentials never travel inside it."
        ),
        keywords=["swarm", "export", "import", "share", "file", "backup", "send"],
    ),
    HelpTopic(
        id="report-bug",
        title="Reporting a bug",
        where="The Help pill, top right, then Report a bug.",
        body=(
            "It writes a diagnostics folder locally (versions, platform, recent log tail, with secrets "
            "stripped), reveals that folder in your file manager, and opens a prefilled GitHub issue to "
            "drag the files into. Nothing uploads on its own."
        ),
        keywords=["bug", "report", "issue", "broken", "diagnostics", "github", "feedback", "crash"],
    ),
]
