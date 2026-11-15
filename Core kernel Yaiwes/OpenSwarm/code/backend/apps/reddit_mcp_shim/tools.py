"""MCP tool surface for Reddit: the full set of things a logged-in human can do.

Reads (browse/search/post/user/inbox/saved) and writes (submit/comment/edit/
delete/vote/save/subscribe/DM). thing ids are Reddit fullnames (t3_=post,
t1_=comment, t4_=message) exactly as returned by the read tools.
"""

OBJ = "object"

TOOLS = [
    {
        "name": "reddit_whoami",
        "description": "Confirm the logged-in Reddit session and return the account name + karma. Use first to verify the session is live.",
        "inputSchema": {"type": OBJ, "properties": {}},
    },
    {
        "name": "reddit_browse",
        "description": "List posts from a subreddit (or the logged-in home feed if subreddit is omitted).",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "subreddit": {"type": "string", "description": "e.g. 'programming'. Omit for your home feed."},
                "sort": {"type": "string", "enum": ["hot", "new", "top", "rising", "best", "controversial"], "default": "hot"},
                "time": {"type": "string", "enum": ["hour", "day", "week", "month", "year", "all"], "description": "For top/controversial."},
                "limit": {"type": "integer", "default": 25, "description": "1-100"},
                "after": {"type": "string", "description": "Pagination cursor from a previous call."},
            },
        },
    },
    {
        "name": "reddit_search",
        "description": "Search posts globally or within a subreddit.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "query": {"type": "string"},
                "subreddit": {"type": "string", "description": "Restrict to this subreddit."},
                "sort": {"type": "string", "enum": ["relevance", "hot", "top", "new", "comments"], "default": "relevance"},
                "time": {"type": "string", "enum": ["hour", "day", "week", "month", "year", "all"], "default": "all"},
                "limit": {"type": "integer", "default": 25},
            },
            "required": ["query"],
        },
    },
    {
        "name": "reddit_get_post",
        "description": "Get a post plus its comment tree. target is a fullname (t3_...), a bare id, or a permalink.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "target": {"type": "string"},
                "comment_limit": {"type": "integer", "default": 50},
            },
            "required": ["target"],
        },
    },
    {
        "name": "reddit_get_user",
        "description": "Get a user's profile (karma, age) plus their recent posts/comments.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "username": {"type": "string"},
                "kind": {"type": "string", "enum": ["overview", "submitted", "comments"], "default": "overview"},
                "limit": {"type": "integer", "default": 25},
            },
            "required": ["username"],
        },
    },
    {
        "name": "reddit_inbox",
        "description": "Read your inbox: messages, replies, mentions, or just unread.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "where": {"type": "string", "enum": ["inbox", "unread", "sent", "messages", "mentions"], "default": "inbox"},
                "limit": {"type": "integer", "default": 25},
            },
        },
    },
    {
        "name": "reddit_my_subreddits",
        "description": "List the subreddits you're subscribed to.",
        "inputSchema": {"type": OBJ, "properties": {"limit": {"type": "integer", "default": 100}}},
    },
    {
        "name": "reddit_saved",
        "description": "List your saved posts and comments (defaults to the logged-in user).",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "username": {"type": "string"},
                "limit": {"type": "integer", "default": 25},
            },
        },
    },
    {
        "name": "reddit_submit",
        "description": "Submit a new post to a subreddit. kind 'self' uses text; kind 'link' uses url.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "subreddit": {"type": "string"},
                "title": {"type": "string"},
                "kind": {"type": "string", "enum": ["self", "link"], "default": "self"},
                "text": {"type": "string", "description": "Markdown body for a self post."},
                "url": {"type": "string", "description": "URL for a link post."},
                "nsfw": {"type": "boolean", "default": False},
                "spoiler": {"type": "boolean", "default": False},
                "send_replies": {"type": "boolean", "default": True},
            },
            "required": ["subreddit", "title"],
        },
    },
    {
        "name": "reddit_comment",
        "description": "Reply to a post or comment. parent_id is a fullname (t3_... for a post, t1_... for a comment, t4_... to reply to a message).",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "parent_id": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["parent_id", "text"],
        },
    },
    {
        "name": "reddit_edit",
        "description": "Edit the text of your own post or comment by fullname.",
        "inputSchema": {
            "type": OBJ,
            "properties": {"thing_id": {"type": "string"}, "text": {"type": "string"}},
            "required": ["thing_id", "text"],
        },
    },
    {
        "name": "reddit_delete",
        "description": "Delete your own post or comment by fullname.",
        "inputSchema": {
            "type": OBJ,
            "properties": {"thing_id": {"type": "string"}},
            "required": ["thing_id"],
        },
    },
    {
        "name": "reddit_vote",
        "description": "Vote on a post or comment. direction: up, down, or clear.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "thing_id": {"type": "string"},
                "direction": {"type": "string", "enum": ["up", "down", "clear"]},
            },
            "required": ["thing_id", "direction"],
        },
    },
    {
        "name": "reddit_save",
        "description": "Save (or unsave) a post or comment by fullname.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "thing_id": {"type": "string"},
                "unsave": {"type": "boolean", "default": False},
            },
            "required": ["thing_id"],
        },
    },
    {
        "name": "reddit_subscribe",
        "description": "Subscribe to (or unsubscribe from) a subreddit by name.",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "subreddit": {"type": "string"},
                "unsubscribe": {"type": "boolean", "default": False},
            },
            "required": ["subreddit"],
        },
    },
    {
        "name": "reddit_send_message",
        "description": "Send a direct message to a user (to = username, no u/ prefix).",
        "inputSchema": {
            "type": OBJ,
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["to", "subject", "text"],
        },
    },
]
