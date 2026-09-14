---
name: morgen-briefing
slug: morgen_briefing
description: Umfassender Tagesplaner — kombiniert Episoden, Kanban-Tasks, Reddit-Leads, Memory und Prioritaeten zu einem strukturierten Plan
trigger_keywords: [Briefing, Morgen, Tagesplan, Ueberblick, Zusammenfassung, was steht an, Plan meinen Tag, Tag planen, Daily Standup, Morning, Guten Morgen, heute, day plan, schedule]
tools_required: [get_recent_episodes, search_memory, kanban_list_tasks, reddit_leads, web_search]
category: productivity
priority: 4
enabled: true
success_count: 0
failure_count: 0
total_uses: 0
avg_score: 0.0
last_used: null
learned_from: [initial-setup]
agent: ""
---

# Morgen-Briefing & Tagesplaner

## Wann anwenden
Wenn der Benutzer den Tag startet, einen Ueberblick haben moechte, oder seinen Tag planen will.

## WICHTIG: Proaktiv und umfassend

Sammle ALLE verfuegbaren Informationsquellen und praesentiere einen strukturierten Tagesplan.
Frage NICHT zuerst — liefere sofort Ergebnisse und biete dann Anpassungen an.

## Ablauf

### Phase 1: Daten sammeln (parallel wo moeglich)

1. **Gestrige Episoden** — Was wurde gestern gemacht?
   Tool: `get_recent_episodes` mit count=3
   Extrahiere: erledigte Aufgaben, offene Punkte, Erkenntnisse

2. **Offene Kanban-Tasks** — Was steht auf dem Board?
   Tool: `kanban_list_tasks` mit status=in_progress
   Tool: `kanban_list_tasks` mit status=backlog (nur high/urgent Priority)
   Extrahiere: faellige Tasks, blockierte Tasks, High-Priority Items

3. **Neue Reddit-Leads** — Gibt es neue Leads zum Bearbeiten?
   Tool: `reddit_leads` mit status=new, min_score=60
   Extrahiere: Anzahl neuer Leads, hoechster Score, wichtigste Subreddits

4. **Memory-Suche** — Offene Todos, Fristen, Termine
   Tool: `search_memory` mit "offen TODO ausstehend Frist Deadline Termin morgen heute"
   Extrahiere: Termine, Fristen, Erinnerungen

5. **Aktuelle Nachrichten** (optional, nur wenn Operation Mode = online/hybrid)
   Tool: `web_search` mit relevanter Branchensuche
   Extrahiere: 1-2 relevante Headlines

### Phase 2: Strukturiertes Briefing praesentieren

Formatiere die Ergebnisse als klaren, actionable Tagesplan:

```
## Guten Morgen, [Owner Name]!

### Rueckblick Gestern
- [Was erledigt wurde — max 3 Punkte]
- [Offene Punkte die mitgenommen werden]

### Dein Tagesplan

**Prioritaet 1 — Sofort erledigen**
- [ ] [Dringendste Aufgabe aus Kanban/Memory]
- [ ] [Zweite dringende Aufgabe]

**Prioritaet 2 — Heute angehen**
- [ ] [Wichtige aber nicht dringende Tasks]
- [ ] [Offene Punkte von gestern]

**Prioritaet 3 — Wenn Zeit bleibt**
- [ ] [Backlog-Items]
- [ ] [Nice-to-haves]

### Reddit-Leads
[X] neue Leads gefunden (hoechster Score: [N])
→ "Willst du die Leads jetzt durchgehen?"

### Erinnerungen
- [Termine/Fristen die heute relevant sind]

### Tipp
[Ein hilfreicher Vorschlag basierend auf den Daten]
```

### Phase 3: Follow-up anbieten

Nach dem Briefing, biete an:
- "Soll ich die Reddit-Leads jetzt scannen/durchgehen?"
- "Soll ich Task X als erstes angehen?"
- "Soll ich den Tagesplan als Kanban-Tasks anlegen?"
- "Moechtest du mehr Details zu einem Punkt?"

## Personalisierung

- Nutze den Owner-Namen aus der Config (config.owner_name)
- Passe den Ton an die Tageszeit an (Morgen: motivierend, Nachmittag: fokussiert)
- Wenn der User regelmaessig Briefings nutzt, erwaehne Fortschritt
- Lerne aus Feedback welche Sektionen der User ueberspringt

## Wenn Daten fehlen

- Kein Kanban: Ueberspringe die Task-Sektion
- Keine Reddit-Leads: Ueberspringe, erwaehne "Social Listening ist nicht konfiguriert"
- Keine Episoden: "Erster Tag? Willkommen!"
- Keine Memory-Treffer: Sektion weglassen

## Cron-Integration

Wenn als Cron-Job eingerichtet (z.B. jeden Morgen um 7:00):
- Automatisches Briefing an den konfigurierten Channel
- Kompakteres Format (keine Follow-up Fragen)
- Endet mit: "Antworte fuer Details oder sage 'Plan anpassen'"

## Bekannte Fallstricke
- Am Montag: Freitag statt "gestern" als Referenz
- Wenn keine Episoden vorhanden: Ehrlich sagen, nicht erfinden
- Nicht zu lang — Briefing soll schnell erfassbar sein (max 300 Woerter)

## Qualitaetskriterien
- Maximal 300 Woerter
- Offene Punkte priorisiert
- Konkrete Handlungsvorschlaege
- Jede Sektion hat mindestens einen actionable Punkt
