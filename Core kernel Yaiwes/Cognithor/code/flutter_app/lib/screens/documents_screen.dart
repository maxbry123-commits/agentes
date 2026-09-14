import 'package:flutter/material.dart';
import 'package:cognithor_ui/l10n/generated/app_localizations.dart';

/// Document Templates & Generation screen.
///
/// Displays available document templates (Brief, Rechnung, Bericht, etc.)
/// and allows the user to fill variables and generate PDFs.
///
/// Backend integration:
///   GET  /api/v1/tools/template_list   → list templates
///   POST /api/v1/tools/template_render → fill + compile
///   POST /api/v1/tools/document_create → structured creation
///   POST /api/v1/tools/typst_render    → raw Typst compilation
class DocumentsScreen extends StatelessWidget {
  const DocumentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.documentsTitle)),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.description_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'Dokument-Vorlagen',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              '6 Vorlagen: Brief, Rechnung, Bericht, Lebenslauf, Protokoll, Angebot',
              style: TextStyle(color: Colors.grey),
            ),
            SizedBox(height: 24),
            Text(
              'Kommt in einem zukuenftigen Update.\n'
              'Nutze den Chat: "Erstelle einen Brief an Firma GmbH"',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
