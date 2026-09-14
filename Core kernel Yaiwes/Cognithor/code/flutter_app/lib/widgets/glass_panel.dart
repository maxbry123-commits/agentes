import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

/// Glassmorphism panel — frosted glass effect with neon-tinted border.
///
/// Use this as the primary card/container widget throughout the app.
/// Replaces CognithorCard for the new Sci-Fi aesthetic.
class GlassPanel extends StatefulWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.tint, // section color tint (default: accent/violet)
    this.borderRadius = 16,
    this.blur = 16,
    this.padding,
    this.glowOnHover = false,
    this.onTap,
  });

  final Widget child;
  final Color? tint;
  final double borderRadius;
  final double blur;
  final EdgeInsets? padding;
  final bool glowOnHover;
  final VoidCallback? onTap;

  @override
  State<GlassPanel> createState() => _GlassPanelState();
}

class _GlassPanelState extends State<GlassPanel> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final color = widget.tint ?? CognithorTheme.accent;
    final isHovered = _hovered && widget.glowOnHover;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final borderAlpha = isDark
        ? (isHovered ? 0.35 : 0.12)
        : (isHovered ? 0.40 : 0.18);

    final fillColor = isDark
        ? color.withValues(alpha: 0.04)
        : color.withValues(alpha: 0.03);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: CognithorTheme.animDuration,
          curve: CognithorTheme.animCurve,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            border: Border.all(
              color: isDark
                  ? color.withValues(alpha: borderAlpha)
                  : Theme.of(context).dividerColor,
              width: 1.0,
            ),
            boxShadow: isHovered
                ? [
                    BoxShadow(
                      color: color.withValues(alpha: isDark ? 0.15 : 0.08),
                      blurRadius: 20,
                      spreadRadius: -2,
                    ),
                  ]
                : null,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            clipBehavior: Clip.antiAlias,
            child: BackdropFilter(
              filter: ImageFilter.blur(
                sigmaX: widget.blur,
                sigmaY: widget.blur,
              ),
              child: Container(
                decoration: BoxDecoration(
                  color: isDark ? fillColor : Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(widget.borderRadius),
                ),
                padding: widget.padding ?? const EdgeInsets.all(16),
                child: widget.child,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
