package models

// Model version pins — updated on each model release.
const (
	ReconModelName      = "ArmurAI/recon-agent-qwen2.5-7b"
	ClassifierModelName = "ArmurAI/classifier-agent-mistral-7b"
	ExploitModelName    = "ArmurAI/exploit-agent-deepseek-r1-8b"
	ReportModelName     = "ArmurAI/report-agent-llama3.1-8b"
)

// AllModels returns the list of all specialist model names.
func AllModels() []string {
	return []string{
		ReconModelName,
		ClassifierModelName,
		ExploitModelName,
		ReportModelName,
	}
}

// ModelInfo describes a specialist model.
type ModelInfo struct {
	Name        string `json:"name"`
	Role        string `json:"role"`
	BaseModel   string `json:"base_model"`
	Description string `json:"description"`
}

// ModelRegistry returns info about all specialist models.
func ModelRegistry() []ModelInfo {
	return []ModelInfo{
		{Name: ReconModelName, Role: "recon", BaseModel: "Qwen/Qwen2.5-7B-Instruct", Description: "Analyzes recon tool output into structured attack surface models"},
		{Name: ClassifierModelName, Role: "classifier", BaseModel: "mistralai/Mistral-7B-Instruct-v0.3", Description: "Maps findings to CVEs, scores CVSS, filters false positives"},
		{Name: ExploitModelName, Role: "exploit", BaseModel: "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", Description: "Constructs multi-step attack chains with chain-of-thought reasoning"},
		{Name: ReportModelName, Role: "report", BaseModel: "meta-llama/Llama-3.1-8B-Instruct", Description: "Generates professional pentest reports"},
	}
}
