import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cognithor_ui/providers/config_provider.dart';
import 'package:cognithor_ui/widgets/form/form_widgets.dart';

class DatabasePage extends StatelessWidget {
  const DatabasePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ConfigProvider>(
      builder: (context, cfg, _) {
        final db = cfg.cfg['database'] as Map<String, dynamic>? ?? {};
        final backend = (db['backend'] ?? 'sqlite').toString();

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            CognithorSelectField.fromStrings(
              label: 'Backend',
              value: backend,
              options: const ['sqlite', 'postgresql'],
              onChanged: (v) => cfg.set('database.backend', v),
            ),
            CognithorToggleField(
              label: 'Encryption',
              value: db['encryption_enabled'] == true,
              onChanged: (v) => cfg.set('database.encryption_enabled', v),
            ),
            if (backend == 'postgresql') ...[
              const Divider(height: 24),
              CognithorTextField(
                label: 'Host',
                value: (db['pg_host'] ?? 'localhost').toString(),
                onChanged: (v) => cfg.set('database.pg_host', v),
              ),
              CognithorNumberField(
                label: 'Port',
                value: (db['pg_port'] as num?) ?? 5432,
                onChanged: (v) => cfg.set('database.pg_port', v),
                min: 1,
                max: 65535,
              ),
              CognithorTextField(
                label: 'Database Name',
                value: (db['pg_dbname'] ?? 'jarvis').toString(),
                onChanged: (v) => cfg.set('database.pg_dbname', v),
              ),
              CognithorTextField(
                label: 'User',
                value: (db['pg_user'] ?? '').toString(),
                onChanged: (v) => cfg.set('database.pg_user', v),
              ),
              CognithorTextField(
                label: 'Password',
                value: (db['pg_password'] ?? '').toString(),
                onChanged: (v) => cfg.set('database.pg_password', v),
                isPassword: true,
                isSecret: true,
              ),
              CognithorNumberField(
                label: 'Pool Min',
                value: (db['pg_pool_min'] as num?) ?? 2,
                onChanged: (v) => cfg.set('database.pg_pool_min', v),
                min: 1,
              ),
              CognithorNumberField(
                label: 'Pool Max',
                value: (db['pg_pool_max'] as num?) ?? 10,
                onChanged: (v) => cfg.set('database.pg_pool_max', v),
                min: 1,
              ),
            ],
          ],
        );
      },
    );
  }
}
