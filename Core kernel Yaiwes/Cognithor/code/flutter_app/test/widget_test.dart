import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cognithor_ui/main.dart';

void main() {
  testWidgets('App builds without error', (WidgetTester tester) async {
    await tester.pumpWidget(const CognithorApp());
    await tester.pump();
    // Smoke check: the widget tree builds successfully (at least one WidgetsApp subtree).
    expect(find.byType(WidgetsApp), findsWidgets);
  });
}
