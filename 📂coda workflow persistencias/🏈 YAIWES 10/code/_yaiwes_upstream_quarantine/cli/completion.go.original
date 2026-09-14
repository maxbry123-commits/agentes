package cli

import (
	"os"

	"github.com/spf13/cobra"
)

// completionCmd emits a shell completion script for bash, zsh, fish, or
// PowerShell using Cobra's built-in generators. Scriptability basics: an
// operator wiring pentestswarm into their shell shouldn't have to hand-roll
// completions.
var completionCmd = &cobra.Command{
	Use:   "completion [bash|zsh|fish|powershell]",
	Short: "Generate shell completion scripts",
	Long: `Generate a shell completion script for pentestswarm.

The script must be evaluated by your shell to enable completions.

Bash:

  $ source <(pentestswarm completion bash)

  # To load completions for every new session, execute once:
  # Linux:
  $ pentestswarm completion bash > /etc/bash_completion.d/pentestswarm
  # macOS (Homebrew bash-completion@2):
  $ pentestswarm completion bash > $(brew --prefix)/etc/bash_completion.d/pentestswarm

Zsh:

  # If shell completion is not already enabled, enable it once:
  $ echo "autoload -U compinit; compinit" >> ~/.zshrc

  # To load completions for every new session, execute once:
  $ pentestswarm completion zsh > "${fpath[1]}/_pentestswarm"

  # You will need to start a new shell for this setup to take effect.

Fish:

  $ pentestswarm completion fish | source

  # To load completions for every new session, execute once:
  $ pentestswarm completion fish > ~/.config/fish/completions/pentestswarm.fish

PowerShell:

  PS> pentestswarm completion powershell | Out-String | Invoke-Expression

  # To load completions for every new session, run:
  PS> pentestswarm completion powershell > pentestswarm.ps1
  # and source this file from your PowerShell profile.
`,
	DisableFlagsInUseLine: true,
	ValidArgs:             []string{"bash", "zsh", "fish", "powershell"},
	Args:                  cobra.MatchAll(cobra.ExactArgs(1), cobra.OnlyValidArgs),
	RunE: func(cmd *cobra.Command, args []string) error {
		switch args[0] {
		case "bash":
			return rootCmd.GenBashCompletionV2(os.Stdout, true)
		case "zsh":
			return rootCmd.GenZshCompletion(os.Stdout)
		case "fish":
			return rootCmd.GenFishCompletion(os.Stdout, true)
		case "powershell":
			return rootCmd.GenPowerShellCompletionWithDesc(os.Stdout)
		}
		return nil // unreachable: cobra.OnlyValidArgs already rejected anything else
	},
}

func init() {
	rootCmd.AddCommand(completionCmd)
}
