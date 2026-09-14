package cli

import (
	"context"
	"sync/atomic"

	"github.com/Armur-Ai/Pentest-Swarm-AI/cli/ui"
	livedash "github.com/Armur-Ai/Pentest-Swarm-AI/internal/dashboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/engine"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	tea "github.com/charmbracelet/bubbletea"
)

// runCampaignTUI runs a campaign with the full-screen Bubble Tea dashboard as
// the live view. The swarm runs in a goroutine and streams events into the
// program via Send; the TUI owns the terminal until the user quits (q / Ctrl-C
// / s). It is the real-event wiring the old `campaign watch` stub never had.
//
// cancel stops the swarm if the user quits mid-run. exitCode is set to 1 when
// the run surfaced findings, matching the scriptable exit-code contract of the
// non-TUI path.
func runCampaignTUI(
	ctx context.Context,
	cancel context.CancelFunc,
	run func(context.Context, engine.CampaignConfig, engine.EventCallback) error,
	cc engine.CampaignConfig,
	target, objective string,
	dash *livedash.Server,
	exitCode *int,
) error {
	model := ui.NewModel("live", target, objective)
	// Let the spend meter fill toward the real per-run cap (0 = no cap, meter
	// grows against a soft ceiling instead).
	model.BudgetUSD = cc.MaxCostUSD
	if dash != nil {
		// Show the web dashboard URL inside the TUI so the user knows the
		// browser view is live in parallel.
		model.DashboardURL = dash.URL()
	}
	prog := tea.NewProgram(model, tea.WithAltScreen())

	var findings int64
	onEvent := func(e pipeline.CampaignEvent) {
		if e.EventType == pipeline.EventFindingDiscovered {
			atomic.AddInt64(&findings, 1)
		}
		prog.Send(ui.EventMsg(e))
		// Feed the same event stream to the web dashboard so both views stay
		// in sync during the run.
		if dash != nil {
			publishToDashboard(dash, e)
		}
	}

	go func() {
		err := run(ctx, cc, onEvent)
		if dash != nil {
			dash.PublishStatus("complete")
		}
		// Tell the TUI the run finished; it switches to the "complete" state
		// and waits for the user to quit so they can read the final board.
		prog.Send(ui.DoneMsg{Err: err})
	}()

	if _, err := prog.Run(); err != nil {
		cancel()
		if dash != nil {
			dash.Stop()
		}
		return err
	}
	// The user quit (or quit after completion); make sure the swarm goroutine
	// is torn down if it's still running, and stop the web dashboard.
	cancel()
	if dash != nil {
		dash.Stop()
	}

	if atomic.LoadInt64(&findings) > 0 {
		*exitCode = 1
	}
	return nil
}
