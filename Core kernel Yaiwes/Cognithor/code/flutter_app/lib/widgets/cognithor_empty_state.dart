import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

class CognithorEmptyState extends StatefulWidget {
  const CognithorEmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.action,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? action;

  @override
  State<CognithorEmptyState> createState() => _CognithorEmptyStateState();
}

class _CognithorEmptyStateState extends State<CognithorEmptyState>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(CognithorTheme.spacingXl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Gradient circle behind the pulsing icon
            ScaleTransition(
              scale: _pulseAnimation,
              child: Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      CognithorTheme.accent.withAlpha(30),
                      CognithorTheme.accent.withAlpha(5),
                    ],
                  ),
                ),
                child: Icon(
                  widget.icon,
                  size: 48,
                  color: CognithorTheme.accent.withAlpha(180),
                ),
              ),
            ),
            const SizedBox(height: CognithorTheme.spacingLg),
            Text(
              widget.title,
              style: theme.textTheme.titleLarge?.copyWith(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            if (widget.subtitle != null) ...[
              const SizedBox(height: CognithorTheme.spacingSm),
              Text(
                widget.subtitle!,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontSize: 13,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
            if (widget.action != null) ...[
              const SizedBox(height: CognithorTheme.spacingLg),
              widget.action!,
            ],
          ],
        ),
      ),
    );
  }
}
