#!/usr/bin/env python3
"""run.py — git (wrapper seguro)"""
import json, sys, os, subprocess

PROTECTED = {"main", "master"}
GITHUB_API = "https://api.github.com"

def sh(cmd, cwd=".", env=None, timeout=60):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env or os.environ)

def main():
    p = json.loads(sys.stdin.read() or "{}")
    action = p["action"]
    repo = p.get("repo", ".")
    force = p.get("force", False)
    pat = os.environ.get("GITHUB_PAT_MAXBRY", "")

    if action == "status":
        r = sh(["git","-C",repo,"status","--short"])
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout}))
    elif action == "branch":
        r = sh(["git","-C",repo,"checkout","-b",p["name"]])
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}))
    elif action == "commit":
        files = p.get("files") or ["."]
        sh(["git","-C",repo,"add","--"] + files)
        r = sh(["git","-C",repo,"commit","-m",p["message"]])
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}))
    elif action == "push":
        if force and p.get("remote","origin").split("/")[-1] in PROTECTED:
            print(json.dumps({"ok": False, "error": "force-push a rama protegida bloqueado"}))
            sys.exit(1)
        remote = p.get("remote","origin")
        branch = p.get("branch") or sh(["git","-C",repo,"rev-parse","--abbrev-ref","HEAD"]).stdout.strip()
        cmd = ["git","-C",repo,"push"]
        if force: cmd.append("--force")
        cmd += [remote, branch]
        env = os.environ.copy()
        if pat:
            env["GIT_ASKPASS"] = "/bin/true"
            env["GITHUB_TOKEN"] = pat
        r = sh(cmd, env=env, timeout=120)
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}))
    elif action == "pr":
        if not pat:
            print(json.dumps({"ok": False, "error": "GITHUB_PAT_MAXBRY no seteado"})); sys.exit(1)
        url = sh(["git","-C",repo,"config","--get","remote.origin.url"]).stdout.strip()
        if url.startswith("git@"):
            url = url.split(":")[-1].replace(".git","")
        else:
            url = url.split("github.com/")[-1].replace(".git","")
        owner, name = url.split("/")
        head = sh(["git","-C",repo,"rev-parse","--abbrev-ref","HEAD"]).stdout.strip()
        body = {"title": p["title"], "head": head, "base": p.get("base","main"), "body": p.get("body","")}
        r = subprocess.run(
            ["curl","-sS","-X","POST", f"{GITHUB_API}/repos/{owner}/{name}/pulls",
             "-H",f"Authorization: token {pat}", "-H","Accept: application/vnd.github+json",
             "-d",json.dumps(body)],
            capture_output=True, text=True, timeout=60,
        )
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout[:2000], "stderr": r.stderr[:1000]}))
    elif action == "clone":
        r = sh(["git","clone",p["url"],p.get("dest",".")], timeout=600)
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}))
    elif action == "diff":
        r = sh(["git","-C",repo,"diff","--stat"])
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout}))
    elif action == "log":
        r = sh(["git","-C",repo,"log","--oneline","-n",str(p.get("n",20))])
        print(json.dumps({"ok": r.returncode == 0, "stdout": r.stdout}))
    else:
        print(json.dumps({"ok": False, "error": f"unknown action: {action}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
