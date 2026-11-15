# Reddit Lead Hunter v2 Flutter + Playwright — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Wizard queue mode, LLM refinement UI, template picker, performance badges, feedback dialog in Flutter + wire Playwright auto-post with cookie persistence.

**Architecture:** 5 new Flutter widgets consume v2 REST APIs. Provider gets ~8 new methods. Wizard is a full-screen overlay accessed from the Leads tab. Playwright auto-post uses BrowserAgent with persistent Reddit session cookies.

**Tech Stack:** Flutter, Provider, Material 3, Python Playwright (BrowserAgent)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `lib/widgets/leads/lead_wizard.dart` | **New** — full-screen wizard for sequential lead processing |
| `lib/widgets/leads/refine_panel.dart` | **New** — LLM refinement + variant selection |
| `lib/widgets/leads/template_picker.dart` | **New** — template selection bottom sheet |
| `lib/widgets/leads/performance_badge.dart` | **New** — engagement score badge |
| `lib/widgets/leads/feedback_dialog.dart` | **New** — manual feedback tag dialog |
| `lib/providers/reddit_leads_provider.dart` | Extend with refine, templates, feedback, discover methods |
| `lib/services/api_client.dart` | Add ~8 new API methods |
| `lib/screens/reddit_leads_screen.dart` | Add "Process Queue" button + performance view |
| `lib/l10n/app_{en,de,zh,ar}.arb` | ~15 new i18n keys |
| `src/jarvis/social/reply.py` | Wire real Playwright auto-post |

---

### Task 1: API client + Provider extensions + i18n

**Files:**
- Modify: `flutter_app/lib/services/api_client.dart`
- Modify: `flutter_app/lib/providers/reddit_leads_provider.dart`
- Modify: `flutter_app/lib/l10n/app_{en,de,zh,ar}.arb`

- [ ] **Step 1: Add i18n keys to all 4 ARB files**

EN keys (add before closing `}`):
```json
  "processQueue": "Process Queue",
  "wizardComplete": "Queue Complete",
  "wizardSummary": "{replied} replied, {skipped} skipped, {archived} archived",
  "improve": "Improve",
  "variants": "Variants",
  "useTemplate": "Use Template",
  "skipLead": "Skip",
  "noTemplates": "No templates saved yet",
  "feedbackTitle": "How did this reply perform?",
  "feedbackConverted": "Converted (user tried product)",
  "feedbackConversation": "Conversation started",
  "feedbackIgnored": "Ignored (no reaction)",
  "feedbackNegative": "Negative (downvoted)",
  "feedbackDeleted": "Deleted by moderator",
  "engagementScore": "Engagement",
  "discoverSubreddits": "Discover Subreddits",
  "discovering": "Discovering..."
```

DE:
```json
  "processQueue": "Queue abarbeiten",
  "wizardComplete": "Queue abgeschlossen",
  "wizardSummary": "{replied} beantwortet, {skipped} uebersprungen, {archived} archiviert",
  "improve": "Verbessern",
  "variants": "Varianten",
  "useTemplate": "Vorlage nutzen",
  "skipLead": "Ueberspringen",
  "noTemplates": "Noch keine Vorlagen gespeichert",
  "feedbackTitle": "Wie hat diese Antwort performt?",
  "feedbackConverted": "Konvertiert (User hat Produkt getestet)",
  "feedbackConversation": "Gespraech entstanden",
  "feedbackIgnored": "Ignoriert (keine Reaktion)",
  "feedbackNegative": "Negativ (Downvotes)",
  "feedbackDeleted": "Vom Moderator geloescht",
  "engagementScore": "Engagement",
  "discoverSubreddits": "Subreddits entdecken",
  "discovering": "Entdecke..."
```

ZH:
```json
  "processQueue": "处理队列",
  "wizardComplete": "队列完成",
  "wizardSummary": "{replied}已回复, {skipped}已跳过, {archived}已归档",
  "improve": "改进",
  "variants": "变体",
  "useTemplate": "使用模板",
  "skipLead": "跳过",
  "noTemplates": "尚无保存的模板",
  "feedbackTitle": "这条回复表现如何?",
  "feedbackConverted": "转化（用户试用了产品）",
  "feedbackConversation": "产生了对话",
  "feedbackIgnored": "被忽略（无反应）",
  "feedbackNegative": "负面（被踩）",
  "feedbackDeleted": "被版主删除",
  "engagementScore": "参与度",
  "discoverSubreddits": "发现子版块",
  "discovering": "发现中..."
```

AR:
```json
  "processQueue": "معالجة الطابور",
  "wizardComplete": "اكتمل الطابور",
  "wizardSummary": "{replied} تم الرد, {skipped} تم التخطي, {archived} تم الأرشفة",
  "improve": "تحسين",
  "variants": "متغيرات",
  "useTemplate": "استخدام قالب",
  "skipLead": "تخطي",
  "noTemplates": "لا توجد قوالب محفوظة بعد",
  "feedbackTitle": "كيف كان أداء هذا الرد؟",
  "feedbackConverted": "تحويل (جرّب المستخدم المنتج)",
  "feedbackConversation": "بدأت محادثة",
  "feedbackIgnored": "تم التجاهل (بدون رد فعل)",
  "feedbackNegative": "سلبي (تصويت سلبي)",
  "feedbackDeleted": "حذفه المشرف",
  "engagementScore": "المشاركة",
  "discoverSubreddits": "اكتشاف المنتديات",
  "discovering": "جارٍ الاكتشاف..."
```

Run `flutter gen-l10n`.

- [ ] **Step 2: Add API client methods**

In `api_client.dart`, add to the Reddit Leads section:

```dart
  Future<Map<String, dynamic>> refineRedditLead(String id, {String hint = '', int variants = 0}) =>
      post('leads/$id/refine', {'hint': hint, 'variants': variants});

  Future<Map<String, dynamic>> getRedditLeadPerformance(String id) =>
      get('leads/$id/performance');

  Future<Map<String, dynamic>> setRedditLeadFeedback(String id, {required String tag, String note = ''}) =>
      patch('leads/$id/feedback', {'tag': tag, 'note': note});

  Future<Map<String, dynamic>> discoverSubreddits([Map<String, dynamic>? body]) =>
      post('leads/discover-subreddits', body ?? {});

  Future<Map<String, dynamic>> getRedditTemplates({String subreddit = ''}) {
    final params = subreddit.isNotEmpty ? '?subreddit=$subreddit' : '';
    return get('leads/templates$params');
  }

  Future<Map<String, dynamic>> createRedditTemplate(Map<String, dynamic> body) =>
      post('leads/templates', body);

  Future<Map<String, dynamic>> deleteRedditTemplate(String id) =>
      delete('leads/templates/$id');
```

- [ ] **Step 3: Extend Provider**

Add to `RedditLeadsProvider`:

```dart
  Future<Map<String, dynamic>> refineLead(String id, {String hint = '', int variants = 0}) async {
    if (_api == null) return {};
    try {
      return await _api!.refineRedditLead(id, hint: hint, variants: variants);
    } catch (_) {
      return {};
    }
  }

  Future<Map<String, dynamic>> getPerformance(String id) async {
    if (_api == null) return {};
    try {
      return await _api!.getRedditLeadPerformance(id);
    } catch (_) {
      return {};
    }
  }

  Future<bool> setFeedback(String id, {required String tag, String note = ''}) async {
    if (_api == null) return false;
    try {
      await _api!.setRedditLeadFeedback(id, tag: tag, note: note);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<List<Map<String, dynamic>>> discoverSubreddits() async {
    if (_api == null) return [];
    try {
      final resp = await _api!.discoverSubreddits();
      return (resp['suggestions'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ?? [];
    } catch (_) {
      return [];
    }
  }

  Future<List<Map<String, dynamic>>> getTemplates({String subreddit = ''}) async {
    if (_api == null) return [];
    try {
      final resp = await _api!.getRedditTemplates(subreddit: subreddit);
      return (resp['templates'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ?? [];
    } catch (_) {
      return [];
    }
  }
```

- [ ] **Step 4: Run flutter analyze + commit**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter gen-l10n && flutter analyze
git add flutter_app/lib/
git commit -m "feat(flutter): v2 API methods + provider extensions + i18n keys"
```

---

### Task 2: PerformanceBadge + FeedbackDialog widgets

**Files:**
- Create: `flutter_app/lib/widgets/leads/performance_badge.dart`
- Create: `flutter_app/lib/widgets/leads/feedback_dialog.dart`

- [ ] **Step 1: Create PerformanceBadge**

Create `flutter_app/lib/widgets/leads/performance_badge.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

class PerformanceBadge extends StatelessWidget {
  const PerformanceBadge({super.key, required this.score, this.compact = false});

  final int score;
  final bool compact;

  Color get _color {
    if (score >= 70) return JarvisTheme.green;
    if (score >= 40) return Colors.orange;
    if (score > 0) return JarvisTheme.red;
    return JarvisTheme.textSecondary;
  }

  @override
  Widget build(BuildContext context) {
    if (score <= 0) return const SizedBox.shrink();

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 4 : 8,
        vertical: compact ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(compact ? 4 : 8),
        border: Border.all(color: _color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.trending_up, size: compact ? 10 : 14, color: _color),
          SizedBox(width: compact ? 2 : 4),
          Text(
            '$score',
            style: TextStyle(
              color: _color,
              fontWeight: FontWeight.w700,
              fontSize: compact ? 9 : 12,
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Create FeedbackDialog**

Create `flutter_app/lib/widgets/leads/feedback_dialog.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

class FeedbackDialog extends StatelessWidget {
  const FeedbackDialog({super.key});

  static const _tags = [
    ('converted', Icons.star, Colors.amber),
    ('conversation', Icons.chat_bubble, Colors.blue),
    ('ignored', Icons.visibility_off, Colors.grey),
    ('negative', Icons.thumb_down, Colors.red),
    ('deleted', Icons.delete, Colors.orange),
  ];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final labels = {
      'converted': l.feedbackConverted,
      'conversation': l.feedbackConversation,
      'ignored': l.feedbackIgnored,
      'negative': l.feedbackNegative,
      'deleted': l.feedbackDeleted,
    };

    return AlertDialog(
      title: Text(l.feedbackTitle),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: _tags.map((t) {
          final (tag, icon, color) = t;
          return ListTile(
            leading: Icon(icon, color: color, size: 22),
            title: Text(labels[tag] ?? tag),
            dense: true,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            onTap: () => Navigator.of(context).pop(tag),
          );
        }).toList(),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(null),
          child: Text(l.cancel),
        ),
      ],
    );
  }
}
```

- [ ] **Step 3: Run flutter analyze + commit**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze
git add flutter_app/lib/widgets/leads/performance_badge.dart flutter_app/lib/widgets/leads/feedback_dialog.dart
git commit -m "feat(flutter): add PerformanceBadge + FeedbackDialog widgets"
```

---

### Task 3: TemplatePicker + RefinePanel widgets

**Files:**
- Create: `flutter_app/lib/widgets/leads/template_picker.dart`
- Create: `flutter_app/lib/widgets/leads/refine_panel.dart`

- [ ] **Step 1: Create TemplatePicker**

Create `flutter_app/lib/widgets/leads/template_picker.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

class TemplatePicker extends StatefulWidget {
  const TemplatePicker({super.key, required this.subreddit});
  final String subreddit;

  @override
  State<TemplatePicker> createState() => _TemplatePickerState();
}

class _TemplatePickerState extends State<TemplatePicker> {
  List<Map<String, dynamic>> _templates = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final templates = await context.read<RedditLeadsProvider>().getTemplates(
      subreddit: widget.subreddit,
    );
    if (mounted) setState(() { _templates = templates; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);

    return DraggableScrollableSheet(
      initialChildSize: 0.5,
      minChildSize: 0.3,
      maxChildSize: 0.8,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _templates.isEmpty
                  ? Center(child: Text(l.noTemplates))
                  : ListView.builder(
                      controller: scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: _templates.length,
                      itemBuilder: (context, i) {
                        final t = _templates[i];
                        return ListTile(
                          title: Text(t['name']?.toString() ?? ''),
                          subtitle: Text(
                            (t['template_text']?.toString() ?? '').replaceAll('\n', ' '),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Text(
                            '${t['use_count'] ?? 0}x',
                            style: TextStyle(color: JarvisTheme.textSecondary, fontSize: 11),
                          ),
                          onTap: () => Navigator.of(context).pop(t['template_text']?.toString() ?? ''),
                        );
                      },
                    ),
        );
      },
    );
  }
}
```

- [ ] **Step 2: Create RefinePanel**

Create `flutter_app/lib/widgets/leads/refine_panel.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';

class RefinePanel extends StatefulWidget {
  const RefinePanel({
    super.key,
    required this.leadId,
    required this.currentDraft,
    required this.onAccept,
  });

  final String leadId;
  final String currentDraft;
  final ValueChanged<String> onAccept;

  @override
  State<RefinePanel> createState() => _RefinePanelState();
}

class _RefinePanelState extends State<RefinePanel> {
  final _hintCtrl = TextEditingController();
  bool _refining = false;
  String? _refinedText;
  List<Map<String, dynamic>> _variants = [];
  int _selectedVariant = -1;

  @override
  void dispose() {
    _hintCtrl.dispose();
    super.dispose();
  }

  Future<void> _refine() async {
    setState(() { _refining = true; _refinedText = null; _variants = []; });
    final result = await context.read<RedditLeadsProvider>().refineLead(
      widget.leadId,
      hint: _hintCtrl.text,
    );
    setState(() {
      _refining = false;
      _refinedText = result['text']?.toString();
    });
  }

  Future<void> _generateVariants() async {
    setState(() { _refining = true; _variants = []; _refinedText = null; _selectedVariant = -1; });
    final result = await context.read<RedditLeadsProvider>().refineLead(
      widget.leadId,
      variants: 3,
    );
    setState(() {
      _refining = false;
      _variants = (result['variants'] as List<dynamic>?)?.cast<Map<String, dynamic>>() ?? [];
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Hint input
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _hintCtrl,
                decoration: InputDecoration(
                  hintText: 'e.g. "make it shorter", "more technical"',
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  border: const OutlineInputBorder(),
                ),
                style: const TextStyle(fontSize: 12),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: _refining ? null : _refine,
              child: _refining
                  ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(l.improve),
            ),
            const SizedBox(width: 4),
            OutlinedButton(
              onPressed: _refining ? null : _generateVariants,
              child: Text(l.variants),
            ),
          ],
        ),

        // Refined result
        if (_refinedText != null) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: JarvisTheme.green.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: JarvisTheme.green.withValues(alpha: 0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Improved:', style: theme.textTheme.labelSmall?.copyWith(color: JarvisTheme.green)),
                const SizedBox(height: 4),
                Text(_refinedText!, style: theme.textTheme.bodySmall),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: ElevatedButton.icon(
                    onPressed: () => widget.onAccept(_refinedText!),
                    icon: const Icon(Icons.check, size: 16),
                    label: const Text('Accept'),
                    style: ElevatedButton.styleFrom(backgroundColor: JarvisTheme.green),
                  ),
                ),
              ],
            ),
          ),
        ],

        // Variants
        if (_variants.isNotEmpty) ...[
          const SizedBox(height: 12),
          ...List.generate(_variants.length, (i) {
            final v = _variants[i];
            final isSelected = _selectedVariant == i;
            return GestureDetector(
              onTap: () => setState(() => _selectedVariant = i),
              child: Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isSelected ? JarvisTheme.accent.withValues(alpha: 0.1) : null,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isSelected ? JarvisTheme.accent : JarvisTheme.textSecondary.withValues(alpha: 0.2),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      v['style']?.toString().toUpperCase() ?? '',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: JarvisTheme.accent),
                    ),
                    const SizedBox(height: 4),
                    Text(v['text']?.toString() ?? '', style: theme.textTheme.bodySmall),
                  ],
                ),
              ),
            );
          }),
          if (_selectedVariant >= 0)
            Align(
              alignment: Alignment.centerRight,
              child: ElevatedButton.icon(
                onPressed: () => widget.onAccept(_variants[_selectedVariant]['text']?.toString() ?? ''),
                icon: const Icon(Icons.check, size: 16),
                label: const Text('Use this variant'),
              ),
            ),
        ],
      ],
    );
  }
}
```

- [ ] **Step 3: Run flutter analyze + commit**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze
git add flutter_app/lib/widgets/leads/template_picker.dart flutter_app/lib/widgets/leads/refine_panel.dart
git commit -m "feat(flutter): add TemplatePicker + RefinePanel widgets"
```

---

### Task 4: Lead Wizard — full-screen sequential processor

**Files:**
- Create: `flutter_app/lib/widgets/leads/lead_wizard.dart`
- Modify: `flutter_app/lib/screens/reddit_leads_screen.dart`

- [ ] **Step 1: Create LeadWizard**

Create `flutter_app/lib/widgets/leads/lead_wizard.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';
import 'package:jarvis_ui/widgets/leads/refine_panel.dart';
import 'package:jarvis_ui/widgets/leads/template_picker.dart';
import 'package:jarvis_ui/widgets/jarvis_toast.dart';

class LeadWizard extends StatefulWidget {
  const LeadWizard({super.key, required this.leads});
  final List<RedditLead> leads;

  @override
  State<LeadWizard> createState() => _LeadWizardState();
}

class _LeadWizardState extends State<LeadWizard> {
  int _currentIndex = 0;
  int _repliedCount = 0;
  int _skippedCount = 0;
  int _archivedCount = 0;
  late TextEditingController _replyCtrl;
  bool _posting = false;
  bool _showRefine = false;

  RedditLead get _currentLead => widget.leads[_currentIndex];
  bool get _isDone => _currentIndex >= widget.leads.length;
  double get _progress => widget.leads.isEmpty ? 1.0 : (_currentIndex / widget.leads.length);

  @override
  void initState() {
    super.initState();
    _replyCtrl = TextEditingController(text: widget.leads.isNotEmpty ? widget.leads[0].effectiveReply : '');
  }

  @override
  void dispose() {
    _replyCtrl.dispose();
    super.dispose();
  }

  void _advance() {
    final next = _currentIndex + 1;
    if (next >= widget.leads.length) {
      setState(() => _currentIndex = next);
      return;
    }
    setState(() {
      _currentIndex = next;
      _replyCtrl.text = widget.leads[next].effectiveReply;
      _showRefine = false;
    });
  }

  Future<void> _reply() async {
    setState(() => _posting = true);
    final provider = context.read<RedditLeadsProvider>();
    if (_replyCtrl.text != _currentLead.effectiveReply) {
      await provider.updateLead(_currentLead.id, replyFinal: _replyCtrl.text);
    }
    final ok = await provider.replyToLead(_currentLead.id);
    setState(() => _posting = false);
    if (ok) {
      _repliedCount++;
      if (mounted) JarvisToast.show(context, 'Reply posted', type: ToastType.success);
      _advance();
    }
  }

  void _skip() {
    _skippedCount++;
    _advance();
  }

  Future<void> _archive() async {
    await context.read<RedditLeadsProvider>().updateLead(_currentLead.id, status: 'archived');
    _archivedCount++;
    _advance();
  }

  Future<void> _pickTemplate() async {
    final text = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (_) => TemplatePicker(subreddit: _currentLead.subreddit),
    );
    if (text != null && text.isNotEmpty && mounted) {
      setState(() => _replyCtrl.text = text);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);

    if (_isDone) return _buildSummary(l, theme);

    final lead = _currentLead;

    return Scaffold(
      appBar: AppBar(
        title: Text('Lead ${_currentIndex + 1}/${widget.leads.length}'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(value: _progress, color: JarvisTheme.accent),
        ),
      ),
      body: KeyboardListener(
        focusNode: FocusNode()..requestFocus(),
        onKeyEvent: (event) {
          if (event is KeyDownEvent) {
            if (event.logicalKey == LogicalKeyboardKey.keyA) _archive();
            if (event.logicalKey == LogicalKeyboardKey.keyS) _skip();
            if (event.logicalKey == LogicalKeyboardKey.keyI) setState(() => _showRefine = !_showRefine);
          }
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Score + subreddit
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: JarvisTheme.accent.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text('${lead.intentScore}/100',
                      style: TextStyle(color: JarvisTheme.accent, fontWeight: FontWeight.w800, fontSize: 18)),
                ),
                const SizedBox(width: 12),
                Text('r/${lead.subreddit}', style: theme.textTheme.titleSmall),
                const Spacer(),
                Text(lead.timeAgo, style: theme.textTheme.bodySmall),
              ],
            ),
            const SizedBox(height: 12),

            // Title + body
            Text(lead.title, style: theme.textTheme.titleMedium),
            if (lead.body.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(lead.body, style: theme.textTheme.bodyMedium),
            ],
            const SizedBox(height: 8),
            if (lead.scoreReason.isNotEmpty)
              Text('Reason: ${lead.scoreReason}',
                  style: theme.textTheme.bodySmall?.copyWith(color: JarvisTheme.textSecondary)),
            const Divider(height: 24),

            // Reply editor
            TextField(
              controller: _replyCtrl,
              maxLines: 6,
              decoration: InputDecoration(
                labelText: l.editReply,
                border: const OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),

            // Tool buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: () => setState(() => _showRefine = !_showRefine),
                  icon: const Icon(Icons.auto_fix_high, size: 16),
                  label: Text(l.improve),
                ),
                OutlinedButton.icon(
                  onPressed: _pickTemplate,
                  icon: const Icon(Icons.description, size: 16),
                  label: Text(l.useTemplate),
                ),
              ],
            ),

            // Refine panel
            if (_showRefine) ...[
              const SizedBox(height: 12),
              RefinePanel(
                leadId: lead.id,
                currentDraft: _replyCtrl.text,
                onAccept: (text) {
                  setState(() {
                    _replyCtrl.text = text;
                    _showRefine = false;
                  });
                },
              ),
            ],
            const SizedBox(height: 24),

            // Action row
            Row(
              children: [
                TextButton.icon(
                  onPressed: _archive,
                  icon: Icon(Icons.archive, size: 16, color: JarvisTheme.textSecondary),
                  label: Text(l.archiveLead, style: TextStyle(color: JarvisTheme.textSecondary)),
                ),
                const Spacer(),
                OutlinedButton.icon(
                  onPressed: _skip,
                  icon: const Icon(Icons.skip_next, size: 16),
                  label: Text(l.skipLead),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: _posting ? null : _reply,
                  icon: _posting
                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.reply, size: 16),
                  label: Text(l.postReply),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text('Shortcuts: A=Archive  S=Skip  I=Improve  R=Reply',
                style: theme.textTheme.bodySmall?.copyWith(color: JarvisTheme.textSecondary, fontSize: 10)),
          ],
        ),
      ),
    );
  }

  Widget _buildSummary(AppLocalizations l, ThemeData theme) {
    return Scaffold(
      appBar: AppBar(title: Text(l.wizardComplete)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, size: 64, color: Colors.green),
            const SizedBox(height: 16),
            Text(l.wizardComplete, style: theme.textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(
              l.wizardSummary(
                replied: _repliedCount.toString(),
                skipped: _skippedCount.toString(),
                archived: _archivedCount.toString(),
              ),
              style: theme.textTheme.bodyLarge,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(l.confirm),
            ),
          ],
        ),
      ),
    );
  }
}
```

Note: `wizardSummary` uses named placeholders. In the ARB file it should be:
```json
"wizardSummary": "{replied} replied, {skipped} skipped, {archived} archived",
"@wizardSummary": { "placeholders": { "replied": { "type": "String" }, "skipped": { "type": "String" }, "archived": { "type": "String" } } }
```
Make sure the EN arb has the `@wizardSummary` with placeholders. The DE/ZH/AR versions also use `{replied}`, `{skipped}`, `{archived}` in their text.

- [ ] **Step 2: Add "Process Queue" button to LeadsScreen**

In `flutter_app/lib/screens/reddit_leads_screen.dart`, add a method:

```dart
  void _openWizard() {
    final provider = context.read<RedditLeadsProvider>();
    final newLeads = provider.leads.where((l) => l.status == 'new').toList()
      ..sort((a, b) => b.intentScore.compareTo(a.intentScore));
    if (newLeads.isEmpty) return;
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => LeadWizard(leads: newLeads)),
    ).then((_) => provider.fetchLeads());
  }
```

Add import for `LeadWizard` and add a button in the toolbar or next to the FAB:

In the `_StatsBar`, add a "Process Queue" button:
```dart
if (provider.newCount > 0)
  ElevatedButton.icon(
    onPressed: () { /* call _openWizard from parent */ },
    icon: const Icon(Icons.playlist_play, size: 18),
    label: Text(l.processQueue),
    style: ElevatedButton.styleFrom(backgroundColor: JarvisTheme.accent),
  ),
```

Since `_StatsBar` is a separate widget, the cleanest way is to add an `onProcessQueue` callback to it, or make the button part of the main screen body.

- [ ] **Step 3: Run flutter analyze + commit**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze
git add flutter_app/lib/widgets/leads/lead_wizard.dart flutter_app/lib/screens/reddit_leads_screen.dart
git commit -m "feat(flutter): add Lead Wizard — sequential queue processing with refine + templates"
```

---

### Task 5: Wire Playwright auto-post with cookie persistence

**Files:**
- Modify: `src/jarvis/social/reply.py`
- Modify: `src/jarvis/gateway/gateway.py`

- [ ] **Step 1: Implement real auto-post in reply.py**

Replace the `_auto_post` placeholder in `src/jarvis/social/reply.py`:

```python
    def _auto_post(self, lead: Lead, reply_text: str) -> ReplyResult:
        """Auto-post via Playwright browser agent with persistent cookies."""
        if self._browser_agent is None:
            log.warning("auto_post_no_browser_falling_back_to_clipboard")
            _copy_to_clipboard(reply_text)
            webbrowser.open(lead.url)
            return ReplyResult(
                success=True, mode=ReplyMode.CLIPBOARD,
                error="Browser agent not available, used clipboard fallback",
            )

        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in async context — schedule as task
            future = asyncio.ensure_future(self._auto_post_async(lead, reply_text))
            # Can't await in sync — fallback to clipboard
            _copy_to_clipboard(reply_text)
            webbrowser.open(lead.url)
            return ReplyResult(
                success=True, mode=ReplyMode.CLIPBOARD,
                error="Auto-post scheduled, clipboard used as immediate fallback",
            )

        # Sync context — run async post
        try:
            result = asyncio.run(self._auto_post_async(lead, reply_text))
            return result
        except Exception as exc:
            log.error("auto_post_failed", lead_id=lead.id, error=str(exc))
            _copy_to_clipboard(reply_text)
            webbrowser.open(lead.url)
            return ReplyResult(
                success=True, mode=ReplyMode.CLIPBOARD,
                error=f"Auto-post failed ({exc}), used clipboard fallback",
            )

    async def _auto_post_async(self, lead: Lead, reply_text: str) -> ReplyResult:
        """Async implementation of Playwright auto-post."""
        agent = self._browser_agent
        try:
            # Start browser with Reddit session (cookies persist)
            started = await agent.start(session_id="reddit_session")
            if not started:
                return ReplyResult(success=False, mode=ReplyMode.AUTO, error="Browser failed to start")

            # Navigate to the post
            await agent.navigate(lead.url)
            await agent.press_key("Escape")  # Dismiss popups

            # Find and click the reply/comment button
            try:
                await agent.click('button[slot="full-post-comment-body-button"]')
            except Exception:
                try:
                    await agent.click('[data-click-id="comments"]')
                except Exception:
                    await agent.click('text=Add a comment')

            # Wait for comment box
            import asyncio
            await asyncio.sleep(1.5)

            # Type the reply
            await agent.fill('div[contenteditable="true"]', reply_text)
            await asyncio.sleep(0.5)

            # Click submit
            try:
                await agent.click('button[type="submit"]')
            except Exception:
                await agent.click('text=Comment')

            await asyncio.sleep(2.0)
            log.info("auto_post_success", lead_id=lead.id, url=lead.url)
            return ReplyResult(success=True, mode=ReplyMode.AUTO)

        except Exception as exc:
            log.error("auto_post_browser_error", lead_id=lead.id, error=str(exc))
            return ReplyResult(success=False, mode=ReplyMode.AUTO, error=str(exc))
```

- [ ] **Step 2: Wire BrowserAgent into the service via gateway**

In `src/jarvis/gateway/gateway.py`, find the post-init block where `_reddit_lead_service` is wired (near the LLM wiring). Add after the LLM wiring:

```python
            # Wire BrowserAgent for auto-post (if available)
            browser_agent = getattr(self, "_browser_agent", None)
            if browser_agent:
                self._reddit_lead_service._poster._browser_agent = browser_agent
```

- [ ] **Step 3: Run lint + tests**

```bash
cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/reply.py src/jarvis/gateway/gateway.py && ruff format src/jarvis/social/reply.py src/jarvis/gateway/gateway.py && python -m pytest tests/test_social/ -x -q --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/social/reply.py src/jarvis/gateway/gateway.py
git commit -m "feat(social): wire Playwright auto-post with Reddit session cookies"
```

---

### Task 6: Integrate feedback + performance into LeadDetailSheet + LeadCard

**Files:**
- Modify: `flutter_app/lib/widgets/leads/lead_detail_sheet.dart`
- Modify: `flutter_app/lib/widgets/leads/lead_card.dart`

- [ ] **Step 1: Add performance badge + feedback button to LeadDetailSheet**

In `lead_detail_sheet.dart`, import:
```dart
import 'package:jarvis_ui/widgets/leads/performance_badge.dart';
import 'package:jarvis_ui/widgets/leads/feedback_dialog.dart';
```

After the metadata section (before the closing `]` of the ListView children), add:

```dart
              // Performance + Feedback (for replied leads)
              if (lead.status == 'replied') ...[
                const Divider(height: 24),
                Row(
                  children: [
                    Text(l.engagementScore, style: theme.textTheme.titleSmall),
                    const SizedBox(width: 8),
                    FutureBuilder<Map<String, dynamic>>(
                      future: context.read<RedditLeadsProvider>().getPerformance(lead.id),
                      builder: (context, snap) {
                        if (!snap.hasData) return const SizedBox.shrink();
                        final perf = snap.data?['performance'] as Map<String, dynamic>?;
                        if (perf == null) return const Text('Not tracked yet');
                        final score = (perf['engagement_score'] as num?)?.toInt() ?? 0;
                        return PerformanceBadge(score: score);
                      },
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: () async {
                        final tag = await showDialog<String>(
                          context: context,
                          builder: (_) => const FeedbackDialog(),
                        );
                        if (tag != null && mounted) {
                          await context.read<RedditLeadsProvider>().setFeedback(lead.id, tag: tag);
                          JarvisToast.show(context, 'Feedback saved', type: ToastType.success);
                        }
                      },
                      icon: const Icon(Icons.feedback, size: 16),
                      label: Text(l.feedbackTitle, style: const TextStyle(fontSize: 11)),
                    ),
                  ],
                ),
              ],
```

- [ ] **Step 2: Add RefinePanel to LeadDetailSheet**

Add import for `RefinePanel` and add it after the reply editor TextField:

```dart
              const SizedBox(height: 8),
              RefinePanel(
                leadId: lead.id,
                currentDraft: _replyCtrl.text,
                onAccept: (text) => setState(() => _replyCtrl.text = text),
              ),
```

- [ ] **Step 3: Run flutter analyze + commit**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze
git add flutter_app/lib/widgets/leads/lead_detail_sheet.dart flutter_app/lib/widgets/leads/lead_card.dart
git commit -m "feat(flutter): integrate performance, feedback, refine into lead views"
```

---

### Task 7: Final verification + full test suite + flutter build

- [ ] **Step 1: flutter analyze**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze
```

- [ ] **Step 2: Ruff lint**

```bash
cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && ruff format --check src/ tests/
```

- [ ] **Step 3: Full Python test suite**

```bash
cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py
```

- [ ] **Step 4: Flutter web build**

```bash
cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter build web --release
```

- [ ] **Step 5: Run verify_all.py**

```bash
cd "D:/Jarvis/jarvis complete v20" && python scripts/verify_all.py
```

- [ ] **Step 6: Push + release**

```bash
git push origin main
```

---

## Self-Review

**Spec coverage:**
- [x] Wizard queue mode → Task 4
- [x] LLM Refinement UI → Task 3 (RefinePanel)
- [x] Template picker → Task 3 (TemplatePicker)
- [x] Performance badge → Task 2
- [x] Feedback dialog → Task 2
- [x] Playwright auto-post → Task 5
- [x] Provider extensions → Task 1
- [x] API client methods → Task 1
- [x] i18n keys → Task 1
- [x] Integration into existing views → Task 6

**Type consistency:** `RedditLead`, `RedditLeadsProvider` methods match API client. `refineLead()` returns Map with `text`/`style` or `variants` list. `wizardSummary` uses named placeholders matching ARB format.
