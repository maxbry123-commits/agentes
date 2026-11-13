import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

/// Thumbs up/down feedback buttons shown below assistant messages.
class FeedbackButtons extends StatefulWidget {
  const FeedbackButtons({
    super.key,
    required this.messageId,
    required this.onFeedback,
  });

  final String messageId;
  final void Function(int rating, String messageId) onFeedback;

  @override
  State<FeedbackButtons> createState() => _FeedbackButtonsState();
}

class _FeedbackButtonsState extends State<FeedbackButtons> {
  int? _rating;

  @override
  Widget build(BuildContext context) {
    if (_rating != null) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            _rating == 1 ? Icons.thumb_up : Icons.thumb_down,
            size: 14,
            color: _rating == 1 ? CognithorTheme.green : CognithorTheme.orange,
          ),
          const SizedBox(width: 4),
          Text(
            _rating == 1 ? 'Danke!' : 'Feedback gesendet',
            style: TextStyle(fontSize: 11, color: CognithorTheme.textSecondary),
          ),
        ],
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _FeedbackIcon(
          icon: Icons.thumb_up_outlined,
          tooltip: 'Gute Antwort',
          onTap: () {
            setState(() => _rating = 1);
            widget.onFeedback(1, widget.messageId);
          },
        ),
        const SizedBox(width: 4),
        _FeedbackIcon(
          icon: Icons.thumb_down_outlined,
          tooltip: 'Nicht hilfreich',
          onTap: () {
            setState(() => _rating = -1);
            widget.onFeedback(-1, widget.messageId);
          },
        ),
      ],
    );
  }
}

class _FeedbackIcon extends StatelessWidget {
  const _FeedbackIcon({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: Icon(icon, size: 16, color: CognithorTheme.textTertiary),
        ),
      ),
    );
  }
}
