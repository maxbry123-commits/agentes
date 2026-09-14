// Property test for clamp_decision() (the only misfire-prone part of the fix).
// Compiles with plain clang, no node/electron/AppKit, so it runs anywhere fast.
// Hammers millions of random window/content/point combinations and asserts the
// three invariants the fix's safety rests on. Run via ./run-tests.sh.
#include "clamp_decision.h"
#include <stdio.h>
#include <stdlib.h>

static unsigned long g_seed = 88172645463325252ULL;
static double frnd(double lo, double hi) {  // xorshift -> [lo,hi)
  g_seed ^= g_seed << 13; g_seed ^= g_seed >> 7; g_seed ^= g_seed << 17;
  return lo + (hi - lo) * ((double)(g_seed >> 11) / (double)(1ULL << 53));
}

static long fails = 0;
static void check(int cond, const char *msg,
                  double px, double py, double w, double h,
                  double cx, double cy, double cw, double ch, ClampDecision d) {
  if (cond) return;
  if (fails < 12)
    fprintf(stderr,
            "FAIL %s: p=(%.2f,%.2f) win=(%.2f,%.2f) content=(%.2f,%.2f,%.2f,%.2f) "
            "=> clamp=%d (%.2f,%.2f)\n",
            msg, px, py, w, h, cx, cy, cw, ch, d.clamp, d.x, d.y);
  fails++;
}

static void run(double px, double py, double w, double h,
                double cx, double cy, double cw, double ch) {
  ClampDecision d = clamp_decision(px, py, w, h, cx, cy, cw, ch);
  int inside = (px >= 0.0 && px < w && py >= 0.0 && py < h);
  if (inside) {
    // INVARIANT 1 (no misfire on normal clicks): in-window release is untouched.
    check(!d.clamp, "inside-must-not-clamp", px, py, w, h, cx, cy, cw, ch, d);
    check(d.x == px && d.y == py, "inside-must-be-identical", px, py, w, h, cx, cy, cw, ch, d);
  } else {
    // INVARIANT 2 (crash-safe): off-window release is clamped strictly inside the
    // content rect, so Chromium's hit-test can never return null.
    check(d.clamp, "outside-must-clamp", px, py, w, h, cx, cy, cw, ch, d);
    check(d.x >= cx + 1.0 && d.x <= cx + cw - 1.0, "x-in-content", px, py, w, h, cx, cy, cw, ch, d);
    check(d.y >= cy + 1.0 && d.y <= cy + ch - 1.0, "y-in-content", px, py, w, h, cx, cy, cw, ch, d);
  }
  // INVARIANT 3: never produces NaN/inf.
  check(d.x == d.x && d.y == d.y, "no-nan", px, py, w, h, cx, cy, cw, ch, d);
}

int main(void) {
  // Hand-picked edges: exact corners, the off-by-one boundaries, second-display
  // negatives, the literal 650->499 case I verified on real events.
  run(0, 0, 500, 350, 0, 0, 500, 350);          // top-left corner (inside)
  run(499, 349, 500, 350, 0, 0, 500, 350);      // last inside pixel
  run(500, 175, 500, 350, 0, 0, 500, 350);      // exactly on right edge (outside)
  run(650, 175, 500, 350, 0, 0, 500, 350);      // the verified real case -> expect x=499
  run(-300, -900, 500, 350, 0, 0, 500, 350);    // second display up-left (negatives)
  run(99999, 99999, 500, 350, 0, 0, 500, 350);  // far off-window

  const long N = 5000000;
  for (long i = 0; i < N; i++) {
    double w = frnd(80, 4000), h = frnd(80, 4000);
    double cw = frnd(50, w), ch = frnd(50, h);
    double cx = frnd(0, w - cw), cy = frnd(0, h - ch);
    double px = frnd(-3000, w + 3000), py = frnd(-3000, h + 3000);
    run(px, py, w, h, cx, cy, cw, ch);
  }

  if (fails) {
    fprintf(stderr, "\nclamp_decision: %ld FAILURES across %ld cases\n", fails, N + 6);
    return 1;
  }
  printf("clamp_decision: ALL %ld cases pass (invariants: in-window untouched, "
         "off-window snapped strictly inside content, no NaN)\n", N + 6);
  return 0;
}
