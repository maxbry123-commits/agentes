import 'package:flutter/material.dart';

/// ARC-AGI-3 Benchmark screen.
///
/// Allows the user to start ARC-AGI-3 game sessions, view scores,
/// and monitor the agent's exploration progress.
///
/// Backend integration:
///   POST /api/v1/tools/arc_play   → start game
///   GET  /api/v1/tools/arc_status → query session
///   GET  /api/v1/tools/arc_replay → replay audit trail
class ArcScreen extends StatelessWidget {
  const ArcScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ARC-AGI-3 Benchmark')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'ARC-AGI-3 Benchmark',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              '25 interaktive Reasoning-Puzzles | CNN + State Graph Agent',
              style: TextStyle(color: Colors.grey),
            ),
            SizedBox(height: 24),
            Text(
              'Kommt in einem zukuenftigen Update.\n'
              'Nutze den Chat: "Spiele ARC-AGI-3 Game ls20"\n'
              'Oder CLI: python -m jarvis.arc --game ls20',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
