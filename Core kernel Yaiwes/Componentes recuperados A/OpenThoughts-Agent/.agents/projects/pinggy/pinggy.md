# Pinggy persistent tunnels — how to invoke & test

Written 2026-06-23. Ground truth = `hpc/pinggy_utils.py`, `eval/jupiter/eval_harbor.sbatch`,
`docs/EVAL_GUIDE.md` §3, and `scripts/inference/serve_public.py`. The bank of 10 pairs
lives at `~/Documents/notes/ot-agent/pinggy_bank.md`.

> **A pinggy "pair" is NOT an HTTP service you can GET to test liveness.** It is an
> **SSH reverse tunnel** whose public hostname is dormant until a tunnel binds it. The
> mistake to avoid: `curl https://<id>.a.pinggy.link/` and reading the HTTP code. That
> returns curl `000` (connection-level failure / no backend) for **every** pair, free or
> in-use, and tells you nothing.

## How a persistent tunnel actually works

- Each pair = (`persistent_url`, `token`), e.g. `dadccqeqqf.a.pinggy.link` / `BXKOoiIRGSc`.
- You open an **SSH reverse tunnel** from the host that runs the local server:
  ```bash
  ssh -p 443 -R0:localhost:<LOCAL_PORT> \
      -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
      <TOKEN>@pro.pinggy.io
  ```
  (`-R0:localhost:PORT` = forward a remote port down to your local port; pinggy maps the
  persistent hostname to that binding.) `PinggyConfig.get_ssh_command()` wraps this in a
  `while true; do … ; sleep 10; done` auto-reconnect loop.
- **Binding is exclusive**: a second tunnel to the same pair is **rejected**
  (EVAL_GUIDE.md §3 "Allocation"). This is the real collision risk — two jobs on one pair
  clobber each other.
- The OpenAI-compatible base is `https://<id>.a.pinggy.link/v1`. For `serve_public.py` the
  base carries the Iris controller proxy path: `https://<id>.a.pinggy.link/proxy/serve.<ep>/v1`.

## The canonical "is this pair live / in-use" probe

From the sbatch connectivity verification and EVAL_GUIDE.md §3 cross-cluster check: hit the
**OpenAI `/v1/models` endpoint** and inspect the **body**, never the root `/` and never the
HTTP code.

In-use (returns a models list → someone is serving on it):
```bash
curl -sk --connect-timeout 5 https://<id>.a.pinggy.link/v1/models | grep -q '"object"' && echo IN-USE || echo FREE
```
Richer (shows which model + its root path, to detect cross-cluster contamination):
```bash
URL=<id>.a.pinggy.link
curl -s --max-time 8 https://$URL/v1/models \
  | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('data',[{}])[0]; print(f\"served={m.get('id')} root={m.get('root','')[:80]}\")"
```
- `root=` not pointing inside your `paths.hf_cache` → pair is contaminated by another
  cluster/account using the same pair → pick a different one.
- Free pair → `/v1/models` returns nothing parseable (pinggy serves a 502/"tunnel
  inactive" HTML page or drops the connection); the `grep`/`json.load` fails.

## Why the naive root-path probe fails

- `curl -o /dev/null -w '%{http_code}' https://<id>.a.pinggy.link/` → `000` for all pairs.
- `000` is curl's "no HTTP transaction completed" (DNS/TCP/TLS failure or reset), **not**
  an HTTP error. The only reliable signal is a real OpenAI response on `/v1/models`.

## ⚠️ ISP DNS poisoning on the laptop (Altice/Optimum) — resolve via 1.1.1.1

On this Mac the ISP DNS returns a **bogus IP** for `*.a.pinggy.link`:
`167.206.37.145` (rDNS `nomproxy-sia.vip.orbgny.alticeusa.net` — a dead Altice proxy node),
which silently **times out**. Meanwhile `pinggy.io` (apex → `75.2.60.5`) and the SSH target
`pro.pinggy.io:443` (`173.255.212.128`) resolve and connect fine. So a plain curl to a
pair URL hangs ~6s and returns `000` **for every pair**, masking the real free/in-use
state. Fix: resolve the real edge via public DNS and force it with `--resolve`:
```bash
EDGE=$(dig @1.1.1.1 +short <id>.a.pinggy.link | tail -1)   # real edge: 172.104.241.200 (Linode)
curl -sk --resolve "<id>.a.pinggy.link:443:$EDGE" https://<id>.a.pinggy.link/v1/models
```
All `*.a.pinggy.link` hostnames share that one pinggy edge IP. To verify the endpoint from
this Mac generally, point `/etc/resolv.conf`/System DNS at `1.1.1.1`/`8.8.8.8`, or add a
`/etc/hosts` line. External testers (correct DNS) are unaffected — only this laptop is.

## Verified pair-occupancy probe (2026-06-23)

With the real edge IP, the free/in-use signal is crisp:
- **FREE pair** (no tunnel bound) → pinggy edge **accepts TCP then resets the TLS handshake**
  ("Connection reset by peer", curl `000` in ~0.2s, NOT a 6s timeout). This is the dormant
  state.
- **IN-USE pair** → `/v1/models` returns OpenAI JSON (`"object":"list"`); use the §3
  collision-check to read `served`/`root`.

```bash
EDGE=$(dig @1.1.1.1 +short dadccqeqqf.a.pinggy.link | tail -1)
for u in $(grep -oE '[a-z0-9]+\.a\.pinggy\.link' ~/Documents/notes/ot-agent/pinggy_bank.md); do
  code=$(curl -sk --connect-timeout 6 --max-time 10 --resolve "${u}:443:${EDGE}" \
    -o /dev/null -w '%{http_code}' "https://${u}/v1/models" 2>/dev/null)
  echo "$u -> ${code:+code=$code; }$([ "$code" = 200 ] && echo IN-USE || echo FREE)"
done
```
Result 2026-06-23: **all 10 pairs FREE**.

> The SSH tunnel itself is unaffected by the DNS poisoning — `serve_public.py` / the sbatch
> dial `pro.pinggy.io:443` (correct IP, open). Only **local verification** of the public URL
> from this Mac is blocked until DNS is fixed; external testers see the live endpoint.

## In-code usage

- `PinggyTunnel.start()` (hpc/pinggy_utils.py) deliberately does **not** health-check via
  the public URL — HPC compute nodes often lack external DNS. It only confirms the SSH
  process is alive after a 5s stabilize window. Liveness is then proven by the sbatch's
  `curl … /v1/models | grep object` loop (6 × 5s retries).
- To stand up a tunnel in Python:
  ```python
  from hpc.pinggy_utils import PinggyConfig, PinggyTunnel
  cfg = PinggyConfig(persistent_url="dadccqeqqf.a.pinggy.link", token="BXKOoiIRGSc",
                     local_port=8000, local_host="localhost")
  with PinggyTunnel(config=cfg, log_path=Path("/tmp/pinggy.log")) as t:
      endpoint = t.public_endpoint   # https://dadccqeqqf.a.pinggy.link/v1
  ```
- `serve_public.py` uses `local_host="127.0.0.1"` (marin-serve's controller proxy), not
  `localhost`.

## Teardown

- The tunnel is just an SSH process. Killing the launching process (Ctrl-C / `kill
  <PID>`) drops the binding and frees the pair immediately — pinggy does not hold it.
- On HPC, cancelling the SLURM job kills the SSH tunnel with it.
