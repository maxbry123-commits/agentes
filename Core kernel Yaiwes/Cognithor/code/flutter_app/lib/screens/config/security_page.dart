import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cognithor_ui/providers/config_provider.dart';
import 'package:cognithor_ui/widgets/form/form_widgets.dart';

class SecurityPage extends StatelessWidget {
  const SecurityPage({super.key});

  static List<String> _toStringList(dynamic v) {
    if (v is List) return v.map((e) => e.toString()).toList();
    return [];
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ConfigProvider>(
      builder: (context, cfg, _) {
        final sec = cfg.cfg['security'] as Map<String, dynamic>? ?? {};

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            CognithorNumberField(
              label: 'Max Iterations',
              value: (sec['max_iterations'] as num?) ?? 10,
              onChanged: (v) => cfg.set('security.max_iterations', v),
              min: 1,
              max: 50,
            ),
            CognithorNumberField(
              label: 'Max Sub-Agent Depth',
              value: (sec['max_sub_agent_depth'] as num?) ?? 3,
              onChanged: (v) => cfg.set('security.max_sub_agent_depth', v),
              min: 1,
              max: 10,
            ),
            CognithorListField(
              label: 'Allowed Paths',
              value: _toStringList(sec['allowed_paths']),
              onChanged: (v) => cfg.set('security.allowed_paths', v),
              placeholder: '/path/to/directory',
            ),
            CognithorListField(
              label: 'Blocked Commands',
              value: _toStringList(sec['blocked_commands']),
              onChanged: (v) => cfg.set('security.blocked_commands', v),
              placeholder: 'rm -rf',
            ),
            CognithorListField(
              label: 'Credential Patterns',
              value: _toStringList(sec['credential_patterns']),
              onChanged: (v) => cfg.set('security.credential_patterns', v),
              placeholder: 'regex pattern',
              description: 'Patterns to detect credentials in output',
            ),
          ],
        );
      },
    );
  }
}
