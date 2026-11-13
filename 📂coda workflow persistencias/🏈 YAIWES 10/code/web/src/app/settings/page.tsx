"use client";

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <h2 className="text-2xl font-bold">Settings</h2>

      {/* Provider */}
      <Section title="LLM Provider">
        <div className="space-y-3">
          <div className="flex gap-3">
            <ProviderOption name="Claude" selected description="Anthropic API — best quality" />
            <ProviderOption name="Ollama" description="Local models — full privacy" />
            <ProviderOption name="LM Studio" description="OpenAI-compatible local server" />
          </div>
          <Input label="API Key" type="password" placeholder="sk-ant-..." />
          <Input label="Model" placeholder="claude-sonnet-4-6" />
        </div>
      </Section>

      {/* Models */}
      <Section title="Specialist Models">
        <div className="space-y-2">
          <ModelRow name="Recon Agent" model="ArmurAI/recon-agent-qwen2.5-7b" status="not pulled" />
          <ModelRow name="Classifier" model="ArmurAI/classifier-agent-mistral-7b" status="not pulled" />
          <ModelRow name="Exploit Agent" model="ArmurAI/exploit-agent-deepseek-r1-8b" status="not pulled" />
          <ModelRow name="Report Agent" model="ArmurAI/report-agent-llama3.1-8b" status="not pulled" />
        </div>
        <button className="mt-3 px-4 py-2 bg-accent/20 text-accent rounded-lg text-sm hover:bg-accent/30 transition-colors">
          Pull All Models
        </button>
      </Section>

      {/* Intelligence */}
      <Section title="Shared Intelligence Network">
        <div className="space-y-2">
          <Toggle label="Enable intelligence sharing (opt-in)" />
          <Toggle label="Share anonymized patterns" />
          <Toggle label="Consume community patterns" />
        </div>
      </Section>

      {/* Integrations */}
      <Section title="Integrations">
        <div className="space-y-2">
          <Input label="Jira URL" placeholder="https://company.atlassian.net" />
          <Input label="Slack Bot Token" type="password" placeholder="xoxb-..." />
          <Input label="SIEM Endpoint" placeholder="syslog://splunk.internal:514" />
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface rounded-lg border border-border p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4">{title}</h3>
      {children}
    </div>
  );
}

function ProviderOption({ name, description, selected }: { name: string; description: string; selected?: boolean }) {
  return (
    <div className={`flex-1 p-3 rounded-lg border cursor-pointer transition-colors ${selected ? "border-accent bg-accent/10" : "border-border hover:border-gray-600"}`}>
      <p className="text-sm font-medium">{name}</p>
      <p className="text-xs text-gray-500 mt-1">{description}</p>
    </div>
  );
}

function Input({ label, type = "text", placeholder }: { label: string; type?: string; placeholder?: string }) {
  return (
    <div>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input type={type} placeholder={placeholder} className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:border-accent focus:outline-none transition-colors" />
    </div>
  );
}

function ModelRow({ name, model, status }: { name: string; model: string; status: string }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-background rounded-lg">
      <div>
        <p className="text-sm">{name}</p>
        <p className="text-xs text-gray-500 font-mono">{model}</p>
      </div>
      <span className="text-xs text-yellow-500">{status}</span>
    </div>
  );
}

function Toggle({ label }: { label: string }) {
  return (
    <label className="flex items-center gap-3 cursor-pointer">
      <div className="w-9 h-5 bg-border rounded-full relative">
        <div className="w-4 h-4 bg-gray-500 rounded-full absolute top-0.5 left-0.5 transition-transform" />
      </div>
      <span className="text-sm text-gray-400">{label}</span>
    </label>
  );
}
