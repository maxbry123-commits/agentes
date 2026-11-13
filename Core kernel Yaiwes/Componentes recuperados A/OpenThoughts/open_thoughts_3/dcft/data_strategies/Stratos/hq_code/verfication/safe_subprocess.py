import fcntl
import os
import signal
import subprocess
import time
from typing import List

MAX_BYTES_PER_READ = 1024
SLEEP_BETWEEN_READS = 0.1


class Result:
    timeout: int
    exit_code: int
    stdout: str
    stderr: str

    def __init__(self, timeout, exit_code, stdout, stderr):
        self.timeout = timeout
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


def set_nonblocking(reader):
    fd = reader.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


def run(
    args: List[str],
    input_str: str,
    timeout_seconds: int = 15,
    max_output_size: int = 2048,
    env=None,
    cwd: str | None = None,
) -> Result:
    """
    Runs the given program with arguments. After the timeout elapses, kills the process
    and all other processes in the process group. Captures at most max_output_size bytes
    of stdout and stderr each, and discards any output beyond that.
    """
    p = subprocess.Popen(
        args,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=MAX_BYTES_PER_READ,
        cwd=cwd,
    )

    if input_str != "":
        p.stdin.write(input_str.encode())
        stdout, stderr = p.communicate(timeout=timeout_seconds)
        exit_code = p.returncode
        p.stdin.close()
    else:
        stdout, stderr = p.communicate(timeout=timeout_seconds)
        exit_code = p.returncode

    timeout = exit_code is None
    return Result(timeout=timeout, exit_code=exit_code, stdout=stdout, stderr=stderr)
