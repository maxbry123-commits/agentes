package orchestrator

// Milestone is a checkpoint the orchestrator tracks progress against.
type Milestone struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Completed   bool   `json:"completed"`
}

// Planner decomposes campaign objectives into milestones.
type Planner struct{}

// NewPlanner creates a new campaign planner.
func NewPlanner() *Planner {
	return &Planner{}
}

// DecomposeObjective breaks an objective into ordered milestones.
func (p *Planner) DecomposeObjective(objective string) []Milestone {
	lower := toLower(objective)

	switch {
	case containsIgnoreCase(lower, "rce") || containsIgnoreCase(lower, "remote code"):
		return []Milestone{
			{Name: "recon_complete", Description: "Full attack surface discovered"},
			{Name: "rce_candidates_identified", Description: "Potential RCE findings classified"},
			{Name: "rce_exploited_or_exhausted", Description: "RCE exploitation attempted on all candidates"},
			{Name: "report_generated", Description: "Professional report generated"},
		}

	case containsIgnoreCase(lower, "bug bounty"):
		return []Milestone{
			{Name: "scope_loaded", Description: "Program scope imported from platform"},
			{Name: "recon_complete", Description: "Full attack surface discovered"},
			{Name: "findings_classified", Description: "All findings classified with CVE/CVSS"},
			{Name: "duplicates_checked", Description: "Duplicate detection completed"},
			{Name: "report_formatted", Description: "Bug bounty compliant report generated"},
		}

	case containsIgnoreCase(lower, "ctf") || containsIgnoreCase(lower, "flag"):
		return []Milestone{
			{Name: "recon_complete", Description: "Machine enumerated"},
			{Name: "initial_foothold", Description: "Initial access achieved"},
			{Name: "user_flag", Description: "User flag captured"},
			{Name: "privilege_escalation", Description: "Root/admin access achieved"},
			{Name: "root_flag", Description: "Root flag captured"},
		}

	default:
		// General "find all vulnerabilities"
		return []Milestone{
			{Name: "recon_complete", Description: "Full attack surface discovered"},
			{Name: "findings_classified", Description: "All findings classified and scored"},
			{Name: "exploitation_attempted", Description: "Top attack chains tested"},
			{Name: "report_generated", Description: "Professional report generated"},
		}
	}
}
