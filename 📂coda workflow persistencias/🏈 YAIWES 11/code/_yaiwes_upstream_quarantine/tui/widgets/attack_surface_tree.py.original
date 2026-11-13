"""AttackSurfaceTree — 攻击面树状视图（渗透模式）。"""
from textual.widgets import Tree


class AttackSurfaceTree(Tree):
    """攻击面树状视图 — 目标 → 端口/服务 → 漏洞。"""

    def on_mount(self):
        self.border_title = "攻击面"
        self.show_root = False

    def update_from_attack_surface(self, attack_surface):
        """从 AttackSurface 对象刷新树。"""
        self.clear()
        if not attack_surface:
            self.root.add("[dim]暂无攻击面数据[/]")
            return

        # 目标分支
        root = self.root
        root.expand()
        target_count = 0
        for host, target in list(attack_surface.targets.items())[:15]:
            target_count += 1
            host_label = f"[bold]{host}[/] [{target.status}]"
            host_node = root.add(host_label, expand=True)
            for port in sorted(target.services.keys())[:10]:
                svc = target.services[port]
                svc_label = f"{svc.port}/{svc.protocol}"
                if svc.service_name:
                    svc_label += f" ({svc.service_name})"
                host_node.add_leaf(svc_label)
        if len(attack_surface.targets) > 15:
            root.add(f"[dim]... 及其他 {len(attack_surface.targets) - 15} 个目标[/]")

        # 漏洞分支
        if attack_surface.findings:
            vuln_root = root.add("[bold red]漏洞发现[/]", expand=True)
            severity_color = {"critical": "red", "high": "yellow",
                              "medium": "cyan", "low": "dim", "info": "dim"}
            for f in attack_surface.findings[:10]:
                color = severity_color.get(f.severity, "dim")
                vuln_root.add_leaf(
                    f"[{color}][{f.severity.upper()}][/] {f.type} — {f.target}"
                )
            if len(attack_surface.findings) > 10:
                vuln_root.add_leaf(
                    f"[dim]... 及其他 {len(attack_surface.findings) - 10} 个漏洞[/]"
                )
