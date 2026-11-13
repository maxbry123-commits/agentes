import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

class CognithorChip extends StatelessWidget {
  const CognithorChip({
    super.key,
    required this.label,
    this.color,
    this.icon,
    this.onTap,
    this.selected = false,
  });

  final String label;
  final Color? color;
  final IconData? icon;
  final VoidCallback? onTap;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final chipColor = color ?? CognithorTheme.accent;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: chipColor.withAlpha(38),
          borderRadius: BorderRadius.circular(CognithorTheme.chipRadius),
          border: selected ? Border.all(color: chipColor, width: 1.5) : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: CognithorTheme.iconSizeSm, color: chipColor),
              const SizedBox(width: 4),
            ],
            Text(
              label,
              style: TextStyle(
                color: chipColor,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
