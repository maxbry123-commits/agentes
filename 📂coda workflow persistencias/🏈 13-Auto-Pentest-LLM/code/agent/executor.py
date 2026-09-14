import paramiko
import time
from typing import Tuple, Optional

class SSHExecutor:
    def __init__(self, hostname, port, username, password=None, key_filename=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.client = None
        self.shell = None

    def connect(self):
        """Establish SSH connection and open a shell."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=10
            )
            # Invoke shell for interactive commands if needed, but for now we might just use exec_command
            # Using exec_command is stateless but easier for single commands. 
            # For persistent context (like cd), we might need an interactive shell or chain commands.
            print(f"[*] Connected to {self.username}@{self.hostname}")
            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def run_command(self, command: str, timeout: int = 60) -> Tuple[str, str, int]:
        """
        Execute a command on the remote server.
        Returns: (stdout, stderr, exit_code)
        """
        if not self.client:
            if not self.connect():
                return "", "Connection failed", -1

        try:
            # We wrap command to ensure we get exit code properly if needed,
            # but paramiko's exec_command allows getting exit status.
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Read output
            out = stdout.read().decode('utf-8', errors='replace').strip()
            err = stderr.read().decode('utf-8', errors='replace').strip()
            exit_code = stdout.channel.recv_exit_status()
            
            return out, err, exit_code
        except Exception as e:
            return "", str(e), -1

    def close(self):
        if self.client:
            self.client.close()
