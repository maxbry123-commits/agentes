import time
from typing import Any, Dict, List, Optional, Sequence, Set, Union, Callable
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status
from rich.text import Text
from rich.align import AlignMethod


class Timer:
    """Simple timer for measuring elapsed time."""

    def __init__(self):
        self.start_time = None
        self.elapsed = 0.0

    def start(self):
        self.start_time = time.time()

    def get_elapsed(self):
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
        return self.elapsed

    def stop(self):
        if self.start_time is not None:
            self.elapsed = time.time() - self.start_time
            self.start_time = None


def get_text_from_message(message: Any) -> str:
    if isinstance(message, str):
        return message
    elif isinstance(message, dict):
        return message.get("content", str(message))
    elif hasattr(message, "content"):
        return str(message.content)
    else:
        return str(message)


def create_panel(
    content: Any,
    title: str,
    border_style: str = "blue",
    title_align: AlignMethod = "center",
) -> Panel:
    return Panel(
        content, title=title, border_style=border_style, title_align=title_align
    )


def escape_markdown_tags(content: str, tags_to_include: Set[str]) -> str:
    return content


def create_paused_run_response_panel(resp: Any) -> Panel:
    return Panel(
        Text("Response paused", style="yellow"), title="Status", border_style="yellow"
    )


def _update_display_panels(
    live_log,
    status,
    message,
    show_message,
    response_content,
    thinking_content,
    timer,
    markdown,
    tags_to_include_in_markdown,
    show_reasoning,
    show_full_reasoning,
):
    current_panels: List[Any] = [status]
    if message and show_message:
        message_content = get_text_from_message(message)
        message_panel = create_panel(
            content=Text(message_content, style="green"),
            title="Message",
            border_style="cyan",
        )
        current_panels.append(message_panel)
    if thinking_content:
        thinking_panel = create_panel(
            content=Text(thinking_content),
            title=f"Thinking ({timer.get_elapsed():.1f}s)",
            border_style="green",
        )
        current_panels.append(thinking_panel)
    if response_content:
        if markdown:
            escaped_content = escape_markdown_tags(
                response_content, tags_to_include_in_markdown
            )
            response_display = Markdown(escaped_content)
        else:
            response_display = Text(response_content)
        response_panel = create_panel(
            content=response_display,
            title=f"Response ({timer.get_elapsed():.1f}s)",
            border_style="magenta",
        )
        current_panels.append(response_panel)
    live_log.update(Group(*current_panels))
    return current_panels


def print_response(
    run_func: Callable[..., Any],
    message: Optional[Union[List, Dict, str, Any]] = None,
    *,
    session_id: Optional[str] = None,
    user_id: Optional[str] = "default",
    messages: Optional[List[Union[Dict, Any]]] = None,
    audio: Optional[Sequence[Any]] = None,
    images: Optional[Sequence[Any]] = None,
    videos: Optional[Sequence[Any]] = None,
    files: Optional[Sequence[Any]] = None,
    stream: Optional[bool] = None,
    stream_intermediate_steps: bool = False,
    markdown: bool = False,
    show_message: bool = True,
    show_reasoning: bool = True,
    show_full_reasoning: bool = False,
    console: Optional[Any] = None,
    tags_to_include_in_markdown: Set[str] = {"think", "thinking"},
    knowledge_filters: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> None:
    """
    Shared print_response utility for both agent and adapter.
    Pass the run method as run_func, and any extra context via kwargs.
    """
    timer = Timer()
    timer.start()
    with Live(console=console) as live_log:
        status = Status(
            "Thinking...", spinner="aesthetic", speed=0.4, refresh_per_second=10
        )
        panels: List[Any] = [status]
        if message and show_message:
            message_content = get_text_from_message(message)
            message_panel = create_panel(
                content=Text(message_content, style="green"),
                title="Message",
                border_style="cyan",
            )
            panels.append(message_panel)
            live_log.update(Group(*panels))
        try:
            prompt = get_text_from_message(message) if message else ""
            run_response = run_func(
                prompt,
                user_id=user_id,
                session_id=session_id,
                messages=messages,
                audio=audio,
                images=images,
                videos=videos,
                files=files,
                stream=stream,
                stream_intermediate_steps=stream_intermediate_steps,
                knowledge_filters=knowledge_filters,
                **kwargs,
            )
            response_content = (
                str(run_response) if run_response else "No response generated"
            )
            panels = _update_display_panels(
                live_log,
                status,
                message,
                show_message,
                response_content,
                "",
                timer,
                markdown,
                tags_to_include_in_markdown,
                show_reasoning,
                show_full_reasoning,
            )
            timer.stop()
            final_panels = [p for p in panels if not isinstance(p, Status)]
            live_log.update(Group(*final_panels))
        except Exception as e:
            error_panel = create_panel(
                content=Text(f"Error: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
            panels.append(error_panel)
            live_log.update(Group(*panels))


def print_panel(title, content="", color="blue", title_align: AlignMethod = "center"):
    with Live() as live_log:
        panel = create_panel(
            content=Text(content, style=color),
            title=title,
            border_style=color,
            title_align=title_align,
        )
        live_log.update(Group(*[panel]))


def print_send_message_result(
    send_func: Callable[[str], Any],
    target_node_id: str,
    message: str,
    *,
    source_node_id: Optional[str] = None,
    console: Optional[Any] = None,
    show_message: bool = True,
    markdown: bool = False,
    **kwargs: Any,
) -> None:
    """
    Pretty print utility specifically for node send_message results.

    Args:
        send_func: Function that sends message (e.g., node.send_message)
        target_node_id: ID of the target node
        message: Message to send
        source_node_id: ID of the source node (optional, will try to auto-detect)
        console: Rich console instance
        show_message: Whether to show the sent message
        markdown: Whether to render response as markdown
        **kwargs: Additional arguments for send_func
    """
    timer = Timer()
    timer.start()

    with Live(console=console) as live_log:
        status = Status(
            f"Sending message to {target_node_id}...",
            spinner="aesthetic",
            speed=0.4,
            refresh_per_second=10,
        )
        panels: List[Any] = [status]

        if show_message:
            # Determine source node ID
            if source_node_id is None:
                if hasattr(send_func, "__self__") and hasattr(
                    send_func.__self__, "node_id"
                ):
                    source_node_id = send_func.__self__.node_id
                else:
                    source_node_id = "Unknown"

            message_panel = create_panel(
                content=Text(message, style="green"),
                title=f"Message from {source_node_id} to {target_node_id}",
                border_style="cyan",
            )
            panels.append(message_panel)
            live_log.update(Group(*panels))

        try:
            result = send_func(message, **kwargs)
            response_content = str(result)
            timer.stop()

            # Remove status and add response panel
            panels = [p for p in panels if not isinstance(p, Status)]

            if markdown:
                response_display = Markdown(response_content)
            else:
                response_display = Text(response_content)

            response_panel = create_panel(
                content=response_display,
                title=f"Response from {target_node_id} ({timer.elapsed:.1f}s)",
                border_style="magenta",
            )
            panels.append(response_panel)

            live_log.update(Group(*panels))

        except Exception as e:
            error_panel = create_panel(
                content=Text(f"Error: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
            panels.append(error_panel)
            live_log.update(Group(*panels))
