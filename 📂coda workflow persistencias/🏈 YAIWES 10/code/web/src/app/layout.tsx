import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "pentestswarm — AI Penetration Testing Dashboard",
  description: "Autonomous AI-powered penetration testing platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-white antialiased">
        <div className="flex h-screen">
          {/* Sidebar */}
          <aside className="w-64 bg-surface border-r border-border flex flex-col">
            <div className="p-4 border-b border-border">
              <h1 className="text-lg font-bold text-accent">pentestswarm</h1>
              <p className="text-xs text-gray-500 mt-1">AI Penetration Testing</p>
            </div>
            <nav className="flex-1 p-3 space-y-1">
              <NavItem href="/" icon="dashboard" label="Dashboard" />
              <NavItem href="/campaigns" icon="target" label="Campaigns" />
              <NavItem href="/findings" icon="shield" label="Findings" />
              <NavItem href="/asm" icon="radar" label="ASM" />
              <NavItem href="/playbooks" icon="book" label="Playbooks" />
              <NavItem href="/intelligence" icon="brain" label="Intelligence" />
              <NavItem href="/settings" icon="settings" label="Settings" />
            </nav>
            <div className="p-3 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                All systems operational
              </div>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}

function NavItem({
  href,
  icon,
  label,
}: {
  href: string;
  icon: string;
  label: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-400 hover:text-white hover:bg-surface-hover transition-colors"
    >
      <span className="w-4 h-4 opacity-60">{icon.charAt(0).toUpperCase()}</span>
      {label}
    </a>
  );
}
