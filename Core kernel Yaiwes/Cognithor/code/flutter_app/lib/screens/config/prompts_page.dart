import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cognithor_ui/providers/config_provider.dart';
import 'package:cognithor_ui/widgets/form/form_widgets.dart';

class PromptsPage extends StatelessWidget {
  const PromptsPage({super.key});

  static const _promptKeys = [
    ('plannerSystem', 'System Prompt (Planner)'),
    ('replanPrompt', 'Replan Prompt'),
    ('escalationPrompt', 'Escalation Prompt'),
    ('policyYaml', 'Policy YAML'),
    ('heartbeatMd', 'Heartbeat Checklist'),
    ('personalityPrompt', 'Personality Prompt'),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<ConfigProvider>(
      builder: (context, cfg, _) {
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            ..._promptKeys.map((entry) {
              final (key, label) = entry;
              return CognithorTextAreaField(
                label: label,
                value: (cfg.prompts[key] ?? '').toString(),
                onChanged: (v) {
                  cfg.prompts[key] = v;
                  cfg.notify();
                },
                rows: 8,
                onReset: () {
                  // Reset to empty triggers backend default on save
                  cfg.prompts[key] = '';
                  cfg.notify();
                },
                resetLabel: 'Reset to Default',
              );
            }),
            CognithorCollapsibleCard(
              title: 'Prompt Evolution',
              icon: Icons.auto_fix_high,
              children: [
                Text(
                  'Prompt evolution allows the system to refine prompts based '
                  'on performance metrics. Enable in the planner config.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}
