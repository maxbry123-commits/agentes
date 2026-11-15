package cli

import "testing"

// applyMode: modes steer the default objective (custom always wins) and ASM
// disables active exploitation unless explicitly overridden.
func TestApplyMode(t *testing.T) {
	if obj, _ := applyMode("ctf", defaultObjective, true, false); obj == defaultObjective {
		t.Error("ctf should rewrite the default objective")
	}
	if obj, _ := applyMode("bugbounty", defaultObjective, true, false); obj == defaultObjective {
		t.Error("bugbounty should rewrite the default objective")
	}
	if obj, _ := applyMode("manual", defaultObjective, true, false); obj != defaultObjective {
		t.Errorf("manual should keep the default objective, got %q", obj)
	}
	custom := "pop the admin panel"
	if obj, _ := applyMode("ctf", custom, true, false); obj != custom {
		t.Errorf("custom objective must win, got %q", obj)
	}
	if _, as := applyMode("asm", defaultObjective, true, false); as {
		t.Error("asm should disable active scan by default")
	}
	if _, as := applyMode("asm", defaultObjective, true, true); !as {
		t.Error("asm must respect an explicit --active-scan=true")
	}
}
