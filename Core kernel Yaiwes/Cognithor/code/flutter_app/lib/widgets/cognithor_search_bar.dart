import 'dart:async';

import 'package:flutter/material.dart';
import 'package:cognithor_ui/theme/cognithor_theme.dart';

class CognithorSearchBar extends StatefulWidget {
  const CognithorSearchBar({
    super.key,
    this.hintText = 'Search…',
    this.onChanged,
    this.onClear,
    this.controller,
  });

  final String hintText;
  final ValueChanged<String>? onChanged;
  final VoidCallback? onClear;
  final TextEditingController? controller;

  @override
  State<CognithorSearchBar> createState() => _CognithorSearchBarState();
}

class _CognithorSearchBarState extends State<CognithorSearchBar> {
  late final TextEditingController _controller;
  Timer? _debounce;

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
    _controller.addListener(_onTextChanged);
  }

  void _onTextChanged() {
    setState(() {});
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), () {
      widget.onChanged?.call(_controller.text);
    });
  }

  void _clear() {
    _controller.clear();
    widget.onClear?.call();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    if (widget.controller == null) {
      _controller.dispose();
    } else {
      _controller.removeListener(_onTextChanged);
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textColor = theme.textTheme.bodyMedium?.color;
    final borderColor = theme.dividerColor;

    return TextField(
      controller: _controller,
      style: TextStyle(color: textColor),
      decoration: InputDecoration(
        hintText: widget.hintText,
        filled: true,
        fillColor: theme.cardColor,
        prefixIcon: Icon(
          Icons.search,
          color: CognithorTheme.textSecondary,
          size: CognithorTheme.iconSizeMd,
        ),
        suffixIcon: _controller.text.isNotEmpty
            ? IconButton(
                icon: Icon(
                  Icons.clear,
                  color: CognithorTheme.textSecondary,
                  size: CognithorTheme.iconSizeSm,
                ),
                onPressed: _clear,
              )
            : null,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(CognithorTheme.cardRadius),
          borderSide: BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(CognithorTheme.cardRadius),
          borderSide: BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(CognithorTheme.cardRadius),
          borderSide: BorderSide(color: CognithorTheme.accent),
        ),
      ),
    );
  }
}
