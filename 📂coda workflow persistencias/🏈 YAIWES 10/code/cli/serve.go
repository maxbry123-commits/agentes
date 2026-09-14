package cli

import (
	"fmt"
	"os"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/api"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/config"
	"github.com/spf13/cobra"
)

var serveCmd = &cobra.Command{
	Use:   "serve",
	Short: "Start the API server and web dashboard",
	Example: `  pentestswarm serve
  pentestswarm serve --port 9090`,
	RunE: func(cmd *cobra.Command, args []string) error {
		port, _ := cmd.Flags().GetInt("port")

		cfg, err := config.Load(cfgFile)
		if err != nil {
			return fmt.Errorf("loading config: %w", err)
		}

		// Check env for API key
		if cfg.Orchestrator.APIKey == "" {
			if key := os.Getenv("PENTESTSWARM_ORCHESTRATOR_API_KEY"); key != "" {
				cfg.Orchestrator.APIKey = key
			} else if key := os.Getenv("ANTHROPIC_API_KEY"); key != "" {
				cfg.Orchestrator.APIKey = key
			}
		}

		fmt.Println(colorCyan(`
  ██████  ██     ██  █████  ██████  ███    ███
  ██      ██     ██ ██   ██ ██   ██ ████  ████
  ███████ ██  █  ██ ███████ ██████  ██ ████ ██
       ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██
  ███████  ███ ███  ██   ██ ██   ██ ██      ██`))
		fmt.Printf("\n  API Server:  http://localhost:%d/api/v1\n", port)
		fmt.Printf("  Health:      http://localhost:%d/api/v1/health\n", port)
		fmt.Printf("  Provider:    %s\n", cfg.Orchestrator.Provider)
		fmt.Println()

		server := api.NewServer(port, cfg)
		return server.Start()
	},
}

func init() {
	serveCmd.Flags().Int("port", 8080, "server port")
	rootCmd.AddCommand(serveCmd)
}
