"""
vps_exec.py — Ejecuta comandos en el VPS vía SSH con pexpect.
Uso: python vps_exec.py "comando"
"""
import sys
import pexpect

VPS_HOST = "95.111.232.89"
VPS_USER = "root"
VPS_PASS = "${VPS_PASSWORD}"
VPS_PORT = 22


def vps_run(cmd: str, timeout: int = 60) -> str:
    """Ejecuta un comando en el VPS y devuelve el output."""
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p {VPS_PORT} {VPS_USER}@{VPS_HOST}",
        timeout=timeout, encoding="utf-8"
    )
    child.expect(["password:", "Password:"], timeout=15)
    child.sendline(VPS_PASS)
    child.expect([r"\$", "#"], timeout=15)
    child.sendline(cmd)
    child.expect(pexpect.TIMEOUT, timeout=timeout)
    output = child.before
    child.sendline("exit")
    child.close()
    return output


def vps_run_multi(commands: list, timeout_per_cmd: int = 60) -> list:
    """Ejecuta múltiples comandos en una sesión SSH."""
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p {VPS_PORT} {VPS_USER}@{VPS_HOST}",
        timeout=timeout_per_cmd * len(commands), encoding="utf-8"
    )
    child.expect(["password:", "Password:"], timeout=15)
    child.sendline(VPS_PASS)
    child.expect([r"\$", "#"], timeout=15)
    outputs = []
    for cmd in commands:
        marker = f"__END_CMD_{len(outputs)}__"
        child.sendline(f"{cmd}; echo {marker}")
        child.expect(marker, timeout=timeout_per_cmd)
        outputs.append(child.before)
    child.sendline("exit")
    child.close()
    return outputs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python vps_exec.py 'comando'")
        sys.exit(1)
    cmd = " ".join(sys.argv[1:])
    print(vps_run(cmd))
