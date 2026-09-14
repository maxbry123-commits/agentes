import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

class CognithorProgressBar extends StatelessWidget {
  const CognithorProgressBar({
    super.key,
    required this.value,
    this.label,
    this.color,
    this.height = 6,
  });

  final double value;
  final String? label;
  final Color? color;
  final double height;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final barColor = color ?? CognithorTheme.accent;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text(label!, style: theme.textTheme.bodySmall),
          ),
        ClipRRect(
          borderRadius: BorderRadius.circular(height / 2),
          child: LinearProgressIndicator(
            value: value.clamp(0.0, 1.0),
            minHeight: height,
            backgroundColor: theme.dividerColor,
            valueColor: AlwaysStoppedAnimation<Color>(barColor),
          ),
        ),
      ],
    );
  }
}
