"""Utilities for PyTorch memory profiling."""

import os
import socket
from pathlib import Path
from typing import Optional

import torch

PREFIX = "TORCH_MEMORY_PROFILE"
TIME_FORMAT_STR: str = "%b_%d_%H_%M_%S"
MAX_NUM_OF_MEM_EVENTS_PER_SNAPSHOT: int = 100000


def start_memory_snapshot(enabled: bool = True) -> None:
    """Start recording PyTorch CUDA memory history.

    Args:
        enabled: Whether to enable memory history recording.
    """
    if not torch.cuda.is_available():
        print(f"{PREFIX}: CUDA unavailable. Not recording memory history")
        return

    if enabled:
        print(f"{PREFIX}: Starting snapshot record_memory_history")
        try:
            torch.cuda.memory._record_memory_history(
                max_entries=MAX_NUM_OF_MEM_EVENTS_PER_SNAPSHOT
            )
            print(f"{PREFIX}: Successfully started memory history recording")
        except Exception as e:
            print(f"{PREFIX}: ERROR - Failed to start memory history recording: {e}")
    else:
        print(f"{PREFIX}: Stopping snapshot record_memory_history")
        try:
            torch.cuda.memory._record_memory_history(enabled=None)
            print(f"{PREFIX}: Successfully stopped memory history recording")
        except Exception as e:
            print(f"{PREFIX}: ERROR - Failed to stop memory history recording: {e}")


def save_memory_snapshot(output_dir: str) -> None:
    """Save PyTorch CUDA memory snapshot to file."""
    if not torch.cuda.is_available():
        print(f"{PREFIX}: CUDA unavailable. Not exporting memory snapshot")
        return

    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"{PREFIX}: Created output directory at: {output_dir}")
    except Exception as e:
        print(f"{PREFIX}: ERROR - Failed to create output directory {output_dir}: {e}")
        return

    # Get local rank for unique filenames
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    host_name = socket.gethostname()
    snapshot_path = output_dir / f"memory_snapshot_{host_name}_rank{local_rank}.pickle"

    try:
        print(f"{PREFIX}: Attempting to save snapshot to: {snapshot_path}")
        torch.cuda.memory._dump_snapshot(str(snapshot_path))
        if snapshot_path.exists():
            size_mb = snapshot_path.stat().st_size / (1024 * 1024)
            print(f"{PREFIX}: Successfully saved snapshot at: {snapshot_path}")
            print(f"{PREFIX}: Snapshot file size: {size_mb:.2f} MB")
        else:
            print(
                f"{PREFIX}: ERROR - Snapshot file was not created at: {snapshot_path}"
            )
    except Exception as e:
        print(f"{PREFIX}: ERROR - Failed to capture memory snapshot: {e}")


def trace_handler(prof: torch.profiler.profile, output_dir: str):
    """Handle PyTorch profiler trace export."""
    print(f"{PREFIX}: ====== Trace handler called ======")
    print(f"{PREFIX}: Profiler state: {prof.profiler.function_events}")
    print(f"{PREFIX}: Current step: {prof.step_num}")

    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"{PREFIX}: Created profiler output directory at: {output_dir}")
    except Exception as e:
        print(
            f"{PREFIX}: ERROR - Failed to create profiler output directory {output_dir}: {e}"
        )
        return

    # Get local rank for unique filenames
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    host_name = socket.gethostname()
    file_prefix = (
        output_dir / f"profile_{host_name}_step{prof.step_num}_rank{local_rank}"
    )
    print(f"{PREFIX}: Using file prefix for outputs: {file_prefix}")

    try:
        # Export Chrome trace
        trace_path = f"{file_prefix}_trace.json"
        print(f"{PREFIX}: Exporting Chrome trace to: {trace_path}")
        try:
            if len(prof.profiler.function_events) > 0:  # Only export if we have events
                prof.export_chrome_trace(trace_path)
                if Path(trace_path).exists():
                    size_mb = Path(trace_path).stat().st_size / (1024 * 1024)
                    print(
                        f"{PREFIX}: Successfully saved Chrome trace at: {trace_path} (size: {size_mb:.2f} MB)"
                    )
                else:
                    print(
                        f"{PREFIX}: ERROR - Chrome trace file was not created at: {trace_path}"
                    )
            else:
                print(f"{PREFIX}: No events to export for Chrome trace")
        except Exception as e:
            print(f"{PREFIX}: ERROR - Failed to export Chrome trace: {e}")

        # Export memory timeline
        if torch.cuda.is_available():
            timeline_path = f"{file_prefix}_timeline.html"
            print(f"{PREFIX}: Exporting memory timeline to: {timeline_path}")
            try:
                if (
                    hasattr(prof.profiler, "memory_stats")
                    and prof.profiler.memory_stats()
                ):  # Only export if we have memory stats
                    prof.export_memory_timeline(
                        timeline_path, device=f"cuda:{local_rank}"
                    )
                    if Path(timeline_path).exists():
                        size_mb = Path(timeline_path).stat().st_size / (1024 * 1024)
                        print(
                            f"{PREFIX}: Successfully saved memory timeline at: {timeline_path} (size: {size_mb:.2f} MB)"
                        )
                    else:
                        print(
                            f"{PREFIX}: ERROR - Memory timeline file was not created at: {timeline_path}"
                        )
                else:
                    print(f"{PREFIX}: No memory stats available to export timeline")
            except Exception as e:
                print(f"{PREFIX}: ERROR - Failed to export memory timeline: {e}")
    except Exception as e:
        print(f"{PREFIX}: ERROR - Failed to export profiler outputs: {e}")

    print(f"{PREFIX}: ====== Trace handler completed ======")


def create_profiler(
    output_dir: Optional[str] = None,
    skip_first: int = 0,
    wait: int = 0,
    warmup: int = 0,
    active: int = 6,
    repeat: int = 1,
):
    """Create a PyTorch profiler instance."""
    print(f"{PREFIX}: Creating profiler with settings:")
    print(f"{PREFIX}: - output_dir: {output_dir}")
    print(f"{PREFIX}: - skip_first: {skip_first}")
    print(f"{PREFIX}: - wait: {wait}")
    print(f"{PREFIX}: - warmup: {warmup}")
    print(f"{PREFIX}: - active: {active}")
    print(f"{PREFIX}: - repeat: {repeat}")

    profiler_kwargs = {
        "activities": [
            torch.profiler.ProfilerActivity.CPU,
            torch.profiler.ProfilerActivity.CUDA,
        ],
        "schedule": torch.profiler.schedule(
            skip_first=skip_first,
            wait=wait,
            warmup=warmup,
            active=active,
            repeat=repeat,
        ),
        "record_shapes": True,
        "profile_memory": True,
        "with_stack": True,
    }

    if output_dir:
        print(f"{PREFIX}: Setting up trace handler for directory: {output_dir}")
        profiler_kwargs["on_trace_ready"] = lambda p: trace_handler(p, output_dir)
    else:
        print(
            f"{PREFIX}: WARNING - No output directory specified, traces will not be saved"
        )

    try:
        profiler = torch.profiler.profile(**profiler_kwargs)
        print(f"{PREFIX}: Successfully created profiler instance")
        print(f"{PREFIX}: Profiler configuration:")
        print(f"{PREFIX}: - has trace handler: {hasattr(profiler, 'on_trace_ready')}")
        print(f"{PREFIX}: - activities: {profiler.activities}")
        print(f"{PREFIX}: - record shapes: {profiler.record_shapes}")
        print(f"{PREFIX}: - profile memory: {profiler.profile_memory}")

        return profiler
    except Exception as e:
        print(f"{PREFIX}: ERROR - Failed to create profiler: {e}")
        raise
