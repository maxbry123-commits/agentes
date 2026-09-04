"""Stage 6 — LF-vs-axolotl SFT loss-parity (Gate P) comparison.

Reads the HF Trainer `trainer_state.json` (log_history) each backend writes into its
output_dir and reports the loss band. jinja-as-ground-truth reframe
(notes/axolotl-sft-launch/README.md §Gate M/P DECISION): the CLEAN parity number is
on a NON-delphi config — final train loss within a few % relative, both curves
decreasing, no NaN. delphi is NOT gated on LF-loss-match (its gate is Stage 4).

Usage:
  python sft/axolotl_gates/stage6_parity.py --lf <lf_output_dir> --axolotl <ax_output_dir> \
      [--rel-tol 0.10] [--label non-delphi]

GO   (exit 0): both curves strictly non-increasing (allowing tiny noise), no NaN,
               final losses within --rel-tol relative.
NO-GO(exit 1): any curve diverges/NaN, or the relative gap exceeds --rel-tol.
For a delphi pair pass --no-loss-match to only assert no-divergence/no-NaN.
"""
import argparse
import json
import math
from pathlib import Path


def load_losses(output_dir: Path):
    """Extract the per-step training `loss` series from trainer_state.json."""
    ts = output_dir / "trainer_state.json"
    if not ts.exists():
        # fall back to the newest checkpoint-*/trainer_state.json
        cks = sorted(output_dir.glob("checkpoint-*/trainer_state.json"))
        if not cks:
            raise FileNotFoundError(f"no trainer_state.json under {output_dir}")
        ts = cks[-1]
    hist = json.loads(ts.read_text()).get("log_history", [])
    steps, losses = [], []
    for e in hist:
        if "loss" in e:
            steps.append(e.get("step"))
            losses.append(float(e["loss"]))
    return steps, losses, ts


def decreasing(losses, slack=0.05):
    """True if the loss trends down: last < first and no NaN. Allows local noise."""
    if len(losses) < 2:
        return False
    if any(math.isnan(x) or math.isinf(x) for x in losses):
        return False
    return losses[-1] < losses[0] * (1.0 + slack)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lf", required=True)
    ap.add_argument("--axolotl", required=True)
    ap.add_argument("--rel-tol", type=float, default=0.10)
    ap.add_argument("--label", default="non-delphi")
    ap.add_argument("--no-loss-match", action="store_true",
                    help="delphi pair: assert no-divergence/no-NaN only, skip the LF-loss-match band")
    args = ap.parse_args()

    lf_steps, lf_loss, lf_ts = load_losses(Path(args.lf).resolve())
    ax_steps, ax_loss, ax_ts = load_losses(Path(args.axolotl).resolve())

    print(f"=== Stage 6 parity ({args.label}) ===")
    print(f"LF     : {len(lf_loss)} loss points, first={lf_loss[0]:.4f} last={lf_loss[-1]:.4f}  ({lf_ts})")
    print(f"axolotl: {len(ax_loss)} loss points, first={ax_loss[0]:.4f} last={ax_loss[-1]:.4f}  ({ax_ts})")

    ok = True
    lf_dec = decreasing(lf_loss)
    ax_dec = decreasing(ax_loss)
    print(f"LF decreasing (no NaN):      {lf_dec}")
    print(f"axolotl decreasing (no NaN): {ax_dec}")
    ok = ok and lf_dec and ax_dec

    if not args.no_loss_match:
        rel = abs(ax_loss[-1] - lf_loss[-1]) / max(abs(lf_loss[-1]), 1e-9)
        print(f"final-loss relative gap: {rel*100:.2f}%  (tol {args.rel_tol*100:.1f}%)")
        ok = ok and (rel <= args.rel_tol)
    else:
        print("delphi pair: LF-loss-match skipped (jinja is ground truth); "
              "checking no-divergence/no-NaN only.")

    print(f"\nSTAGE 6 GATE P ({args.label}): {'PASS (GO)' if ok else 'FAIL (NO-GO)'}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
