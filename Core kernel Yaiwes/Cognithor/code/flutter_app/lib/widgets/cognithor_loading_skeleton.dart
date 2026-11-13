import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';
import 'package:shimmer/shimmer.dart';

class CognithorLoadingSkeleton extends StatelessWidget {
  const CognithorLoadingSkeleton({
    super.key,
    this.width,
    this.height = 16,
    this.borderRadius = 8,
    this.count = 1,
  });

  final double? width;
  final double height;
  final double borderRadius;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Theme.of(context).cardColor,
      highlightColor: Theme.of(context).dividerColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: List.generate(count, (i) {
          return Padding(
            padding: EdgeInsets.only(top: i > 0 ? CognithorTheme.spacingSm : 0),
            child: Container(
              width: width,
              height: height,
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(borderRadius),
              ),
            ),
          );
        }),
      ),
    );
  }
}
