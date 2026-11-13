---
name: reddit-lead-hunter
slug: reddit_lead_hunter
description: Scannt Reddit nach High-Intent-Posts und generiert Reply-Drafts
trigger_keywords: [Reddit, Lead, Leads scannen, Social Listening, Reddit Scan, Reddit Monitoring, Leads finden, Reddit suchen, Community Monitoring]
tools_required: [reddit_scan, reddit_leads, reddit_reply, reddit_refine, reddit_discover_subreddits, reddit_templates]
category: marketing
priority: 7
enabled: true
agent: ""
---

# Reddit Lead Hunter

## PFLICHT: Nutze reddit_scan — NICHT web_search!
Fuer Reddit-Aufgaben MUSST du `reddit_scan` verwenden. NIEMALS `web_search` als Ersatz nutzen!
`reddit_scan` greift DIREKT auf Reddit-Daten zu (oeffentliche JSON-Feeds, kein API-Key noetig).
Es liefert BESSERE Ergebnisse als eine Web-Suche: Intent-Scoring, Reply-Drafts, Lead-Tracking.

Deine Reddit-Tools:
- `reddit_scan(subreddits, min_score)` — Scannt Subreddits, scored Posts, erstellt Reply-Drafts
- `reddit_leads(status, min_score, limit)` — Listet gespeicherte Leads
- `reddit_reply(lead_id, mode)` — Kopiert Reply in Zwischenablage + oeffnet Browser
- `reddit_refine(lead_id, hint, variants)` — Verbessert Reply-Draft per LLM
- `reddit_discover_subreddits(product_name, product_description)` — Findet relevante Subreddits
- `reddit_templates(action, subreddit, name, text)` — Template-Verwaltung

## Wann anwenden
Wenn der Benutzer Reddit nach Leads scannen moechte, Social Listening betreiben will, oder nach relevanten Reddit-Diskussionen sucht.

## WICHTIG: Erst Kontext klaeren, dann scannen

Bevor du `reddit_scan` aufrufst, MUSST du folgende Informationen haben:

### 1. Produkt/Thema (PFLICHT)
Frage den User: **"Zu welchem Produkt oder Thema soll ich nach Leads suchen?"**
- Beispiel: "Cognithor", "mein SaaS-Tool", "unser Open-Source-Projekt"
- Brauche: Name UND eine Ein-Satz-Beschreibung

### 2. Subreddits (PFLICHT)
Frage den User: **"In welchen Subreddits soll ich suchen?"**
- Schlage relevante Subreddits vor basierend auf dem Produkt
- Beispiele: r/LocalLLaMA, r/SaaS, r/Python, r/MachineLearning, r/agentframework
- Akzeptiere auch "du entscheidest" - dann waehle 3-5 passende Subreddits

### 3. Antwort-Ton (OPTIONAL)
Frage nur wenn der User Antworten posten moechte:
**"In welchem Ton sollen die Antworten formuliert sein?"**
- Standard: "hilfsbereit, technisch glaubwuerdig, kein Verkaufsgespraech"
- Alternativen: "casual", "technisch detailliert", "kurz und knapp"

### 4. Minimum-Score (OPTIONAL)
Standard ist 60. Nur aendern wenn der User es explizit will.

## Ablauf

1. **Kontext sammeln**: Frage nach Produkt, Subreddits, Ton (siehe oben)
2. **Scan starten**: `reddit_scan` mit den gesammelten Parametern
   - subreddits: kommagetrennte Liste
   - min_score: Standard 60 oder vom User gewuenscht
3. **Ergebnisse praesentieren**: Zeige Leads sortiert nach Score
   - Fuer jeden Lead: Score, Subreddit, Titel, kurze Begruendung
   - Hebe die besten Leads (Score >= 80) besonders hervor
4. **Naechste Schritte anbieten**:
   - "Soll ich auf einen der Leads antworten?"
   - "Soll ich den Scan regelmaessig wiederholen?"
   - "Soll ich die Subreddits anpassen?"

## Beispiel-Dialog

User: "Scanne Reddit nach Leads"
Du: "Gerne! Zu welchem Produkt oder Thema soll ich nach Leads suchen?"
User: "Cognithor - ein Open-Source Agent Operating System"
Du: "In welchen Subreddits soll ich suchen? Ich schlage vor: r/LocalLLaMA, r/SaaS, r/Python, r/agentframework"
User: "Ja, die sind gut"
Du: *ruft reddit_scan auf*
Du: "Ich habe 5 Leads gefunden: [Ergebnisse]"

## Wenn der User auf einen Lead antworten will

1. Zeige den Reply-Draft
2. Frage: "Soll ich den Entwurf anpassen, oder so absenden?"
3. `reddit_reply` mit lead_id und mode=clipboard
4. Erklaere: "Der Text ist in deiner Zwischenablage. Ich habe den Post geoeffnet - einfach Ctrl+V zum Einfuegen."

## Wenn Konfiguration bereits vorhanden
Wenn social.reddit_product_name bereits gesetzt ist, nutze die gespeicherte Konfiguration.
Frage trotzdem: "Soll ich mit den gespeicherten Einstellungen scannen (Produkt: {name}, Subreddits: {list})?"

## Hinweise
- Ergebnisse werden in der Datenbank gespeichert (Duplikate automatisch erkannt)
- Leads koennen auch ueber die Flutter UI verwaltet werden
- Auto-Post (Playwright) nur wenn vom User explizit aktiviert
- Kein Reddit API-Key noetig - nutzt oeffentliche JSON-Feeds
