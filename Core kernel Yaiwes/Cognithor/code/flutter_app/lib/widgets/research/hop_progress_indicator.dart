import 'package:flutter/material.dart';

/// Animated progress indicator shown while a research task is running.
///
/// Displays a spinner with a "Researching…" message. Can be upgraded later
/// to show real hop-by-hop progress once the backend streams status events.
class HopProgressIndicator extends StatelessWidget {
  /// Optional label shown below the spinner. Defaults to "Researching…".
  final String? message;

  const HopProgressIndicator({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final label = message ?? 'Researching\u2026';

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(
            width: 48,
            height: 48,
            child: CircularProgressIndicator(strokeWidth: 3),
          ),
          const SizedBox(height: 16),
          Text(
            label,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'This may take up to 2 minutes for deep research.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant.withValues(alpha: 0.6),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
