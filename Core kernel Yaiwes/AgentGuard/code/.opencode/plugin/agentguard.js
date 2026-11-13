const { Validator } = require('ai-agentguard');

export const AgentGuardPlugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input, output) => {
      // Only validate bash/shell commands
      if (input.tool !== 'bash' && input.tool !== 'execute_bash') {
        return;
      }

      const command = output.args?.command;
      if (!command) {
        return;
      }

      // Validate through AgentGuard
      const validator = new Validator();
      const result = validator.validate(command);

      if (result.action === 'block') {
        throw new Error(`🚫 AgentGuard BLOCKED: ${command}\nReason: ${result.reason}`);
      }

      if (result.action === 'confirm') {
        throw new Error(`⚠️ AgentGuard CONFIRM required: ${command}\nThis command requires manual confirmation. Run it directly in terminal.`);
      }
    },
  };
};