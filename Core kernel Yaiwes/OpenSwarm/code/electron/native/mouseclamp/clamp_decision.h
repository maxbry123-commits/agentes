// Pure geometry for the off-window mouse-release clamp: no AppKit, no state, no I/O,
// so the SAME code that ships in production (mouseclamp.mm includes this) can be
// hammered by a standalone property test (clamp_decision_test.c). Keeping the
// decision here, not inline in the .mm, is the whole point: the misfire risk lives
// in this arithmetic, so this arithmetic is what the machine must prove.
//
// Contract (mirrors NSPointInRect: min-edge inclusive, max-edge exclusive):
//   release INSIDE the window  -> {clamp=false}, location returned UNCHANGED.
//   release OUTSIDE the window -> {clamp=true},  location snapped strictly inside
//                                 the content rect (so Chromium's hit-test can
//                                 never return null, which is the crash).
#ifndef MOUSECLAMP_DECISION_H
#define MOUSECLAMP_DECISION_H

#include <math.h>
#include <stdbool.h>

typedef struct {
  bool clamp;   // replace the event with one at (x,y)? false => leave it alone
  double x, y;  // snapped location; meaningful only when clamp == true
} ClampDecision;

// p  = release location in window coords
// w  = window size (winW, winH)
// c  = content rect in window coords (cx, cy, cw, ch)
static inline ClampDecision clamp_decision(double px, double py,
                                           double winW, double winH,
                                           double cx, double cy,
                                           double cw, double ch) {
  ClampDecision d;
  // inside the window (titlebar included) -> untouched, byte-for-byte the same event
  if (px >= 0.0 && px < winW && py >= 0.0 && py < winH) {
    d.clamp = false;
    d.x = px;
    d.y = py;
    return d;
  }
  d.clamp = true;
  d.x = fmin(fmax(px, cx + 1.0), cx + cw - 1.0);
  d.y = fmin(fmax(py, cy + 1.0), cy + ch - 1.0);
  return d;
}

#endif  // MOUSECLAMP_DECISION_H
