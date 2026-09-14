# Reddit Lead Hunter Flutter Frontend — Implementation Plan (Part B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the 7th Flutter tab "Reddit Leads" with lead pipeline view, detail sheet, reply editor, scan trigger, and stats — consuming the REST API from Plan A.

**Architecture:** New `RedditLeadsProvider` polls `/api/v1/leads` every 30s. `RedditLeadsScreen` shows a filterable lead list with score badges, status chips. `LeadDetailSheet` (bottom sheet) shows full post, editable reply, and action buttons. Navigation wired as 7th tab with Ctrl+7 shortcut.

**Tech Stack:** Flutter, Provider, Material 3, AppLocalizations i18n

**Depends on:** Plan A (Backend) which provides 6 REST endpoints at `/api/v1/leads/*`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `lib/providers/reddit_leads_provider.dart` | **New** — state management, API calls, polling |
| `lib/services/api_client.dart` | Add 6 Reddit Leads API methods |
| `lib/screens/reddit_leads_screen.dart` | **New** — 7th tab, lead list, toolbar, FAB |
| `lib/widgets/leads/lead_card.dart` | **New** — single lead list item |
| `lib/widgets/leads/lead_detail_sheet.dart` | **New** — bottom sheet with reply editor |
| `lib/screens/main_shell.dart` | Add 7th tab + shortcut |
| `lib/main.dart` | Register RedditLeadsProvider |
| `lib/l10n/app_{en,de,zh,ar}.arb` | ~15 new i18n keys |

---

### Task 1: i18n keys + API client methods

**Files:**
- Modify: `flutter_app/lib/l10n/app_{en,de,zh,ar}.arb`
- Modify: `flutter_app/lib/services/api_client.dart`

- [ ] **Step 1: Add i18n keys to app_en.arb**

Before the closing `}`, add:

```json
  "redditLeads": "Leads",
  "@redditLeads": {},
  "noLeadsFound": "No leads found yet",
  "@noLeadsFound": {},
  "noLeadsHint": "Configure your product and subreddits in Settings, then scan Reddit",
  "@noLeadsHint": {},
  "scanNow": "Scan Now",
  "@scanNow": {},
  "scanning": "Scanning...",
  "@scanning": {},
  "leadScore": "Score: {score}",
  "@leadScore": { "placeholders": { "score": { "type": "int" } } },
  "leadNew": "New",
  "@leadNew": {},
  "leadReviewed": "Reviewed",
  "@leadReviewed": {},
  "leadReplied": "Replied",
  "@leadReplied": {},
  "leadArchived": "Archived",
  "@leadArchived": {},
  "draftReply": "Draft Reply",
  "@draftReply": {},
  "editReply": "Edit Reply",
  "@editReply": {},
  "postReply": "Post Reply",
  "@postReply": {},
  "copyReply": "Copy Reply",
  "@copyReply": {},
  "openOnReddit": "Open on Reddit",
  "@openOnReddit": {},
  "markReviewed": "Mark Reviewed",
  "@markReviewed": {},
  "archiveLead": "Archive",
  "@archiveLead": {},
  "intentScore": "Intent Score",
  "@intentScore": {},
  "scoreReason": "Reason",
  "@scoreReason": {},
  "leadStats": "Lead Statistics",
  "@leadStats": {},
  "filterAll": "All",
  "@filterAll": {}
```

- [ ] **Step 2: Add corresponding keys to app_de.arb**

```json
  "redditLeads": "Leads",
  "noLeadsFound": "Noch keine Leads gefunden",
  "noLeadsHint": "Konfiguriere Produkt und Subreddits in den Einstellungen, dann scanne Reddit",
  "scanNow": "Jetzt scannen",
  "scanning": "Scanne...",
  "leadScore": "Score: {score}",
  "leadNew": "Neu",
  "leadReviewed": "Geprueft",
  "leadReplied": "Beantwortet",
  "leadArchived": "Archiviert",
  "draftReply": "Antwortentwurf",
  "editReply": "Antwort bearbeiten",
  "postReply": "Antwort posten",
  "copyReply": "Antwort kopieren",
  "openOnReddit": "Auf Reddit oeffnen",
  "markReviewed": "Als geprueft markieren",
  "archiveLead": "Archivieren",
  "intentScore": "Intent-Score",
  "scoreReason": "Begruendung",
  "leadStats": "Lead-Statistiken",
  "filterAll": "Alle"
```

- [ ] **Step 3: Add corresponding keys to app_zh.arb and app_ar.arb**

ZH:
```json
  "redditLeads": "潜在客户",
  "noLeadsFound": "尚未发现潜在客户",
  "noLeadsHint": "在设置中配置产品和子版块，然后扫描Reddit",
  "scanNow": "立即扫描",
  "scanning": "扫描中...",
  "leadScore": "分数: {score}",
  "leadNew": "新",
  "leadReviewed": "已审核",
  "leadReplied": "已回复",
  "leadArchived": "已归档",
  "draftReply": "回复草稿",
  "editReply": "编辑回复",
  "postReply": "发布回复",
  "copyReply": "复制回复",
  "openOnReddit": "在Reddit上打开",
  "markReviewed": "标记为已审核",
  "archiveLead": "归档",
  "intentScore": "意图分数",
  "scoreReason": "原因",
  "leadStats": "潜在客户统计",
  "filterAll": "全部"
```

AR:
```json
  "redditLeads": "العملاء المحتملون",
  "noLeadsFound": "لم يتم العثور على عملاء محتملين بعد",
  "noLeadsHint": "قم بتكوين المنتج والمنتديات في الإعدادات، ثم امسح Reddit",
  "scanNow": "مسح الآن",
  "scanning": "جارٍ المسح...",
  "leadScore": "النتيجة: {score}",
  "leadNew": "جديد",
  "leadReviewed": "تمت المراجعة",
  "leadReplied": "تم الرد",
  "leadArchived": "مؤرشف",
  "draftReply": "مسودة الرد",
  "editReply": "تعديل الرد",
  "postReply": "نشر الرد",
  "copyReply": "نسخ الرد",
  "openOnReddit": "فتح في Reddit",
  "markReviewed": "تعيين كمراجع",
  "archiveLead": "أرشفة",
  "intentScore": "درجة النية",
  "scoreReason": "السبب",
  "leadStats": "إحصائيات العملاء",
  "filterAll": "الكل"
```

- [ ] **Step 4: Run flutter gen-l10n**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter gen-l10n`

- [ ] **Step 5: Add API methods to api_client.dart**

In `flutter_app/lib/services/api_client.dart`, add before the closing `}` of the class:

```dart
  // ---------------------------------------------------------------------------
  // Reddit Leads
  // ---------------------------------------------------------------------------

  Future<Map<String, dynamic>> scanRedditLeads([Map<String, dynamic>? body]) =>
      post('leads/scan', body ?? {});

  Future<Map<String, dynamic>> getRedditLeads({
    String? status,
    int? minScore,
    int limit = 50,
    int offset = 0,
  }) {
    final params = <String>['limit=$limit', 'offset=$offset'];
    if (status != null && status.isNotEmpty) params.add('status=$status');
    if (minScore != null) params.add('min_score=$minScore');
    return get('leads?${params.join('&')}');
  }

  Future<Map<String, dynamic>> getRedditLead(String id) => get('leads/$id');

  Future<Map<String, dynamic>> updateRedditLead(String id, Map<String, dynamic> body) =>
      patch('leads/$id', body);

  Future<Map<String, dynamic>> replyToRedditLead(String id, {String mode = 'clipboard'}) =>
      post('leads/$id/reply', {'mode': mode});

  Future<Map<String, dynamic>> getRedditLeadStats() => get('leads/stats');
```

- [ ] **Step 6: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 7: Commit**

```bash
git add flutter_app/lib/l10n/ flutter_app/lib/services/api_client.dart
git commit -m "feat(flutter): add i18n keys + API client methods for Reddit Leads"
```

---

### Task 2: RedditLeadsProvider

**Files:**
- Create: `flutter_app/lib/providers/reddit_leads_provider.dart`
- Modify: `flutter_app/lib/main.dart`

- [ ] **Step 1: Create the provider**

Create `flutter_app/lib/providers/reddit_leads_provider.dart`:

```dart
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:jarvis_ui/services/api_client.dart';

/// A single Reddit lead.
class RedditLead {
  RedditLead.fromJson(Map<String, dynamic> json)
      : id = json['id']?.toString() ?? '',
        postId = json['post_id']?.toString() ?? '',
        subreddit = json['subreddit']?.toString() ?? '',
        title = json['title']?.toString() ?? '',
        body = json['body']?.toString() ?? '',
        url = json['url']?.toString() ?? '',
        author = json['author']?.toString() ?? '',
        intentScore = (json['intent_score'] as num?)?.toInt() ?? 0,
        scoreReason = json['score_reason']?.toString() ?? '',
        replyDraft = json['reply_draft']?.toString() ?? '',
        replyFinal = json['reply_final']?.toString() ?? '',
        status = json['status']?.toString() ?? 'new',
        upvotes = (json['upvotes'] as num?)?.toInt() ?? 0,
        numComments = (json['num_comments'] as num?)?.toInt() ?? 0,
        detectedAt = (json['detected_at'] as num?)?.toDouble() ?? 0;

  final String id;
  final String postId;
  final String subreddit;
  final String title;
  final String body;
  final String url;
  final String author;
  final int intentScore;
  final String scoreReason;
  String replyDraft;
  String replyFinal;
  String status;
  final int upvotes;
  final int numComments;
  final double detectedAt;

  String get effectiveReply => replyFinal.isNotEmpty ? replyFinal : replyDraft;

  String get timeAgo {
    final diff = DateTime.now().difference(
        DateTime.fromMillisecondsSinceEpoch((detectedAt * 1000).toInt()));
    if (diff.inDays > 0) return '${diff.inDays}d ago';
    if (diff.inHours > 0) return '${diff.inHours}h ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
    return 'just now';
  }
}

/// State management for the Reddit Leads tab.
class RedditLeadsProvider extends ChangeNotifier {
  ApiClient? _api;
  Timer? _pollTimer;

  List<RedditLead> _leads = [];
  Map<String, dynamic> _stats = {};
  bool _loading = false;
  bool _scanning = false;
  String? _error;
  String _statusFilter = '';
  int _minScoreFilter = 0;

  List<RedditLead> get leads => _leads;
  Map<String, dynamic> get stats => _stats;
  bool get loading => _loading;
  bool get scanning => _scanning;
  String? get error => _error;
  String get statusFilter => _statusFilter;
  int get minScoreFilter => _minScoreFilter;

  int get newCount => _leads.where((l) => l.status == 'new').length;
  int get reviewedCount => _leads.where((l) => l.status == 'reviewed').length;
  int get repliedCount => _leads.where((l) => l.status == 'replied').length;

  void init(ApiClient api) {
    _api = api;
    fetchLeads();
    fetchStats();
    _startPolling();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      fetchLeads();
      fetchStats();
    });
  }

  void setStatusFilter(String status) {
    _statusFilter = status;
    fetchLeads();
  }

  void setMinScoreFilter(int score) {
    _minScoreFilter = score;
    fetchLeads();
  }

  Future<void> fetchLeads() async {
    if (_api == null) return;
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final resp = await _api!.getRedditLeads(
        status: _statusFilter.isEmpty ? null : _statusFilter,
        minScore: _minScoreFilter > 0 ? _minScoreFilter : null,
      );
      if (resp.containsKey('error')) {
        _error = resp['error'].toString();
      } else {
        final list = resp['leads'] as List<dynamic>? ?? [];
        _leads = list
            .map((j) => RedditLead.fromJson(j as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      _error = e.toString();
    }
    _loading = false;
    notifyListeners();
  }

  Future<void> fetchStats() async {
    if (_api == null) return;
    try {
      final resp = await _api!.getRedditLeadStats();
      if (!resp.containsKey('error')) {
        _stats = resp['stats'] as Map<String, dynamic>? ?? {};
      }
    } catch (_) {}
    notifyListeners();
  }

  Future<bool> scanNow() async {
    if (_api == null) return false;
    _scanning = true;
    notifyListeners();
    try {
      final resp = await _api!.scanRedditLeads();
      _scanning = false;
      if (resp.containsKey('error')) {
        _error = resp['error'].toString();
        notifyListeners();
        return false;
      }
      await fetchLeads();
      await fetchStats();
      return true;
    } catch (e) {
      _scanning = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> updateLead(String id, {String? status, String? replyFinal}) async {
    if (_api == null) return false;
    try {
      final body = <String, dynamic>{};
      if (status != null) body['status'] = status;
      if (replyFinal != null) body['reply_final'] = replyFinal;
      final resp = await _api!.updateRedditLead(id, body);
      if (!resp.containsKey('error')) {
        await fetchLeads();
        return true;
      }
    } catch (_) {}
    return false;
  }

  Future<bool> replyToLead(String id, {String mode = 'clipboard'}) async {
    if (_api == null) return false;
    try {
      final resp = await _api!.replyToRedditLead(id, mode: mode);
      if (resp['success'] == true) {
        await fetchLeads();
        return true;
      }
    } catch (_) {}
    return false;
  }
}
```

- [ ] **Step 2: Register in main.dart**

Add import after line 25:
```dart
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
```

Add provider after `RobotOfficeProvider()` line (~60):
```dart
ChangeNotifierProvider(create: (_) => RedditLeadsProvider()),
```

- [ ] **Step 3: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 4: Commit**

```bash
git add flutter_app/lib/providers/reddit_leads_provider.dart flutter_app/lib/main.dart
git commit -m "feat(flutter): add RedditLeadsProvider — state management for leads tab"
```

---

### Task 3: LeadCard widget

**Files:**
- Create: `flutter_app/lib/widgets/leads/lead_card.dart`

- [ ] **Step 1: Create the widget**

Create `flutter_app/lib/widgets/leads/lead_card.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';
import 'package:jarvis_ui/widgets/neon_card.dart';

class LeadCard extends StatelessWidget {
  const LeadCard({
    super.key,
    required this.lead,
    this.onTap,
    this.onReply,
    this.onArchive,
  });

  final RedditLead lead;
  final VoidCallback? onTap;
  final VoidCallback? onReply;
  final VoidCallback? onArchive;

  Color _scoreColor(int score) {
    if (score >= 80) return JarvisTheme.green;
    if (score >= 60) return JarvisTheme.accent;
    if (score >= 40) return Colors.orange;
    return JarvisTheme.red;
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'new': return JarvisTheme.accent;
      case 'reviewed': return Colors.orange;
      case 'replied': return JarvisTheme.green;
      case 'archived': return JarvisTheme.textSecondary;
      default: return JarvisTheme.textSecondary;
    }
  }

  String _statusLabel(AppLocalizations l, String status) {
    switch (status) {
      case 'new': return l.leadNew;
      case 'reviewed': return l.leadReviewed;
      case 'replied': return l.leadReplied;
      case 'archived': return l.leadArchived;
      default: return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final scoreColor = _scoreColor(lead.intentScore);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: NeonCard(
        tint: scoreColor,
        glowOnHover: true,
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: score badge + subreddit + status chip
            Row(
              children: [
                // Score badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: scoreColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: scoreColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    '${lead.intentScore}',
                    style: TextStyle(
                      color: scoreColor,
                      fontWeight: FontWeight.w800,
                      fontSize: 14,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Subreddit
                Text(
                  'r/${lead.subreddit}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: JarvisTheme.textSecondary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                // Status chip
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _statusColor(lead.status).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    _statusLabel(l, lead.status),
                    style: TextStyle(
                      color: _statusColor(lead.status),
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Title
            Text(
              lead.title,
              style: theme.textTheme.titleSmall,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            // Meta row
            DefaultTextStyle(
              style: theme.textTheme.bodySmall?.copyWith(
                color: JarvisTheme.textSecondary,
                fontSize: 11,
              ) ?? const TextStyle(fontSize: 11),
              child: Row(
                children: [
                  Text('u/${lead.author}'),
                  const SizedBox(width: 8),
                  Text('${lead.upvotes} upvotes'),
                  const SizedBox(width: 8),
                  Text('${lead.numComments} comments'),
                  const Spacer(),
                  Text(lead.timeAgo),
                ],
              ),
            ),
            // Action buttons
            if (lead.status != 'archived') ...[
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (lead.status == 'new')
                    TextButton.icon(
                      onPressed: onArchive,
                      icon: Icon(Icons.archive_outlined, size: 14, color: JarvisTheme.textSecondary),
                      label: Text(l.archiveLead, style: TextStyle(fontSize: 11, color: JarvisTheme.textSecondary)),
                      style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8)),
                    ),
                  if (lead.effectiveReply.isNotEmpty)
                    TextButton.icon(
                      onPressed: onReply,
                      icon: Icon(Icons.reply, size: 14, color: scoreColor),
                      label: Text(l.copyReply, style: TextStyle(fontSize: 11, color: scoreColor)),
                      style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8)),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 2: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add flutter_app/lib/widgets/leads/lead_card.dart
git commit -m "feat(flutter): add LeadCard widget — scored lead list item"
```

---

### Task 4: LeadDetailSheet

**Files:**
- Create: `flutter_app/lib/widgets/leads/lead_detail_sheet.dart`

- [ ] **Step 1: Create the widget**

Create `flutter_app/lib/widgets/leads/lead_detail_sheet.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';
import 'package:jarvis_ui/widgets/jarvis_toast.dart';

class LeadDetailSheet extends StatefulWidget {
  const LeadDetailSheet({super.key, required this.lead});
  final RedditLead lead;

  @override
  State<LeadDetailSheet> createState() => _LeadDetailSheetState();
}

class _LeadDetailSheetState extends State<LeadDetailSheet> {
  late final TextEditingController _replyCtrl;
  bool _posting = false;

  @override
  void initState() {
    super.initState();
    _replyCtrl = TextEditingController(text: widget.lead.effectiveReply);
  }

  @override
  void dispose() {
    _replyCtrl.dispose();
    super.dispose();
  }

  Future<void> _copyReply() async {
    await Clipboard.setData(ClipboardData(text: _replyCtrl.text));
    if (mounted) {
      final l = AppLocalizations.of(context);
      JarvisToast.show(context, l.copyReply, type: ToastType.success);
    }
  }

  Future<void> _openOnReddit() async {
    final uri = Uri.tryParse(widget.lead.url);
    if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _postReply() async {
    setState(() => _posting = true);
    final provider = context.read<RedditLeadsProvider>();
    // Save edited reply first
    if (_replyCtrl.text != widget.lead.effectiveReply) {
      await provider.updateLead(widget.lead.id, replyFinal: _replyCtrl.text);
    }
    final ok = await provider.replyToLead(widget.lead.id);
    setState(() => _posting = false);
    if (ok && mounted) {
      final l = AppLocalizations.of(context);
      JarvisToast.show(context, l.postReply, type: ToastType.success);
      Navigator.of(context).pop();
    }
  }

  Future<void> _markReviewed() async {
    await context.read<RedditLeadsProvider>().updateLead(widget.lead.id, status: 'reviewed');
    if (mounted) Navigator.of(context).pop();
  }

  Future<void> _archive() async {
    await context.read<RedditLeadsProvider>().updateLead(widget.lead.id, status: 'archived');
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final lead = widget.lead;

    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.3,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: ListView(
            controller: scrollController,
            padding: const EdgeInsets.all(20),
            children: [
              // Drag handle
              Center(
                child: Container(
                  width: 40, height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: JarvisTheme.textSecondary.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Score + subreddit header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: JarvisTheme.accent.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '${lead.intentScore}/100',
                      style: TextStyle(
                        color: JarvisTheme.accent,
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text('r/${lead.subreddit}',
                      style: theme.textTheme.titleSmall?.copyWith(color: JarvisTheme.textSecondary)),
                  const Spacer(),
                  Text('u/${lead.author}', style: theme.textTheme.bodySmall),
                ],
              ),
              const SizedBox(height: 12),

              // Title
              Text(lead.title, style: theme.textTheme.titleLarge),
              const SizedBox(height: 8),

              // Body
              if (lead.body.isNotEmpty) ...[
                Text(lead.body, style: theme.textTheme.bodyMedium),
                const SizedBox(height: 12),
              ],

              // Score reason
              if (lead.scoreReason.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: JarvisTheme.accent.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(l.scoreReason,
                          style: theme.textTheme.labelSmall?.copyWith(color: JarvisTheme.accent)),
                      const SizedBox(height: 4),
                      Text(lead.scoreReason, style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Reply editor
              Text(l.editReply, style: theme.textTheme.titleSmall),
              const SizedBox(height: 8),
              TextField(
                controller: _replyCtrl,
                maxLines: 6,
                decoration: InputDecoration(
                  border: const OutlineInputBorder(),
                  hintText: l.draftReply,
                ),
              ),
              const SizedBox(height: 16),

              // Action buttons
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ElevatedButton.icon(
                    onPressed: _posting ? null : _postReply,
                    icon: _posting
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.reply, size: 18),
                    label: Text(l.postReply),
                  ),
                  OutlinedButton.icon(
                    onPressed: _copyReply,
                    icon: const Icon(Icons.copy, size: 18),
                    label: Text(l.copyReply),
                  ),
                  OutlinedButton.icon(
                    onPressed: _openOnReddit,
                    icon: const Icon(Icons.open_in_new, size: 18),
                    label: Text(l.openOnReddit),
                  ),
                  if (lead.status == 'new')
                    TextButton.icon(
                      onPressed: _markReviewed,
                      icon: const Icon(Icons.check, size: 18),
                      label: Text(l.markReviewed),
                    ),
                  if (lead.status != 'archived')
                    TextButton.icon(
                      onPressed: _archive,
                      icon: Icon(Icons.archive, size: 18, color: JarvisTheme.textSecondary),
                      label: Text(l.archiveLead,
                          style: TextStyle(color: JarvisTheme.textSecondary)),
                    ),
                ],
              ),

              // Metadata
              const SizedBox(height: 16),
              DefaultTextStyle(
                style: theme.textTheme.bodySmall?.copyWith(
                  color: JarvisTheme.textSecondary.withValues(alpha: 0.6),
                  fontSize: 10,
                ) ?? const TextStyle(fontSize: 10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${lead.upvotes} upvotes  |  ${lead.numComments} comments  |  ${lead.timeAgo}'),
                    Text('Post ID: ${lead.postId}'),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
```

- [ ] **Step 2: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add flutter_app/lib/widgets/leads/lead_detail_sheet.dart
git commit -m "feat(flutter): add LeadDetailSheet — reply editor + actions"
```

---

### Task 5: RedditLeadsScreen + Navigation wiring

**Files:**
- Create: `flutter_app/lib/screens/reddit_leads_screen.dart`
- Modify: `flutter_app/lib/screens/main_shell.dart`

- [ ] **Step 1: Create the screen**

Create `flutter_app/lib/screens/reddit_leads_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:jarvis_ui/l10n/generated/app_localizations.dart';
import 'package:jarvis_ui/providers/connection_provider.dart';
import 'package:jarvis_ui/providers/reddit_leads_provider.dart';
import 'package:jarvis_ui/theme/jarvis_theme.dart';
import 'package:jarvis_ui/widgets/jarvis_empty_state.dart';
import 'package:jarvis_ui/widgets/jarvis_stat.dart';
import 'package:jarvis_ui/widgets/leads/lead_card.dart';
import 'package:jarvis_ui/widgets/leads/lead_detail_sheet.dart';

class RedditLeadsScreen extends StatefulWidget {
  const RedditLeadsScreen({super.key});

  @override
  State<RedditLeadsScreen> createState() => _RedditLeadsScreenState();
}

class _RedditLeadsScreenState extends State<RedditLeadsScreen> {
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _initialized = true;
      final conn = context.read<ConnectionProvider>();
      if (conn.state == JarvisConnectionState.connected) {
        context.read<RedditLeadsProvider>().init(conn.api);
      }
    }
  }

  void _openDetail(RedditLead lead) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => LeadDetailSheet(lead: lead),
    );
  }

  Future<void> _scanNow() async {
    await context.read<RedditLeadsProvider>().scanNow();
  }

  void _archiveLead(String id) {
    context.read<RedditLeadsProvider>().updateLead(id, status: 'archived');
  }

  void _replyLead(String id) {
    context.read<RedditLeadsProvider>().replyToLead(id);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);

    return Consumer<RedditLeadsProvider>(
      builder: (context, provider, _) {
        return Scaffold(
          body: Column(
            children: [
              // Stats bar
              _StatsBar(provider: provider),
              // Filter row
              _FilterRow(provider: provider),
              // Lead list
              Expanded(
                child: provider.loading && provider.leads.isEmpty
                    ? const Center(child: CircularProgressIndicator())
                    : provider.leads.isEmpty
                        ? JarvisEmptyState(
                            icon: Icons.track_changes,
                            title: l.noLeadsFound,
                            subtitle: l.noLeadsHint,
                          )
                        : RefreshIndicator(
                            onRefresh: () => provider.fetchLeads(),
                            child: ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              itemCount: provider.leads.length,
                              itemBuilder: (context, i) {
                                final lead = provider.leads[i];
                                return LeadCard(
                                  lead: lead,
                                  onTap: () => _openDetail(lead),
                                  onReply: () => _replyLead(lead.id),
                                  onArchive: () => _archiveLead(lead.id),
                                );
                              },
                            ),
                          ),
              ),
            ],
          ),
          floatingActionButton: FloatingActionButton.extended(
            onPressed: provider.scanning ? null : _scanNow,
            icon: provider.scanning
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.radar),
            label: Text(provider.scanning ? l.scanning : l.scanNow),
            backgroundColor: JarvisTheme.accent,
          ),
        );
      },
    );
  }
}

class _StatsBar extends StatelessWidget {
  const _StatsBar({required this.provider});
  final RedditLeadsProvider provider;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Wrap(
        spacing: 12,
        runSpacing: 8,
        children: [
          JarvisStat(
            label: 'New',
            value: '${provider.newCount}',
            icon: Icons.fiber_new,
            color: JarvisTheme.accent,
          ),
          JarvisStat(
            label: 'Reviewed',
            value: '${provider.reviewedCount}',
            icon: Icons.check_circle_outline,
            color: Colors.orange,
          ),
          JarvisStat(
            label: 'Replied',
            value: '${provider.repliedCount}',
            icon: Icons.reply,
            color: JarvisTheme.green,
          ),
        ],
      ),
    );
  }
}

class _FilterRow extends StatelessWidget {
  const _FilterRow({required this.provider});
  final RedditLeadsProvider provider;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Row(
        children: [
          SegmentedButton<String>(
            segments: [
              ButtonSegment(value: '', label: Text(l.filterAll)),
              ButtonSegment(value: 'new', label: Text(l.leadNew)),
              ButtonSegment(value: 'reviewed', label: Text(l.leadReviewed)),
              ButtonSegment(value: 'replied', label: Text(l.leadReplied)),
            ],
            selected: {provider.statusFilter},
            onSelectionChanged: (s) => provider.setStatusFilter(s.first),
            style: ButtonStyle(
              visualDensity: VisualDensity.compact,
              textStyle: WidgetStatePropertyAll(
                Theme.of(context).textTheme.labelSmall,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2: Wire into main_shell.dart**

In `flutter_app/lib/screens/main_shell.dart`:

a) Add import at the top:
```dart
import 'package:jarvis_ui/screens/reddit_leads_screen.dart';
```

b) Add to `_screens` list (after `KanbanScreen()`):
```dart
const RedditLeadsScreen(),
```

c) Add to `navItems` list (after the Kanban NavItem):
```dart
NavItem(
  icon: Icons.track_changes_outlined,
  selectedIcon: Icons.track_changes,
  label: l.redditLeads,
  shortcut: '^7',
),
```

d) Add keyboard shortcut (find the Ctrl+6 binding, add after it):
```dart
const SingleActivator(LogicalKeyboardKey.digit7, control: true): () => _navigateTab(6),
```

- [ ] **Step 3: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 4: Commit**

```bash
git add flutter_app/lib/screens/reddit_leads_screen.dart flutter_app/lib/screens/main_shell.dart
git commit -m "feat(flutter): add Reddit Leads as 7th tab with full screen + navigation"
```

---

### Task 6: Final integration + flutter analyze + full test suite

- [ ] **Step 1: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 2: Run Python lint**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && ruff format --check src/ tests/`
Expected: All checks passed

- [ ] **Step 3: Run full Python test suite**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py`
Expected: 13,000+ passed

- [ ] **Step 4: Build Flutter web**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter build web --release`

- [ ] **Step 5: Final commit + push**

```bash
git add -A
git commit -m "feat: complete Reddit Leads Flutter tab — 7th screen with pipeline view

Closes Plan B. Full lead management UI: filterable list, score badges,
status workflow, detail sheet with reply editor, Scan Now FAB."
git push origin main
```

---

## Self-Review

**Spec coverage:**
- [x] LeadsProvider → Task 2
- [x] LeadsScreen (7th tab) → Task 5
- [x] LeadCard → Task 3
- [x] LeadDetailSheet → Task 4
- [x] Navigation wiring → Task 5
- [x] API client methods → Task 1
- [x] i18n keys → Task 1
- [x] main.dart registration → Task 2

**Placeholder scan:** No TBDs. All code blocks complete.

**Type consistency:** `RedditLead` used consistently. `RedditLeadsProvider` method names match API client methods. Status strings ('new'/'reviewed'/'replied'/'archived') match backend LeadStatus enum.
