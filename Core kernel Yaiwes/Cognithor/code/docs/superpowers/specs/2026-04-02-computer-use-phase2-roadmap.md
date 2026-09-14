# Computer Use Phase 2 — Roadmap

**Ziel:** Cognithor soll autonom Desktop-Anwendungen steuern, durch Inhalte scrollen, Informationen extrahieren und strukturiert ablegen.

**Referenz-Szenario:**
> "Oeffne die Anwendung 'Reddit' auf meinem Computer, gib oben in die Zeile bei 'Find Anything' ein: /locallama. Scrolle die letzten 10 Posts und erzeuge jeweils eine Zusammenfassung. Lege diese dann in der neu erstellten Datei 'Reddit_fetch_[heutiges Datum ohne Punkte]' ab und informiere mich darueber, wo die Datei abgelegt wurde — gib mir den Link dorthin."

---

## Sub-Projekt 2A: Vision Engine

**Status:** Offen
**Abhaengigkeit:** Keine (Phase 1 Computer Use ist fertig)

### Was gebaut wird
- VisionAnalyzer Desktop-Integration (API-Mismatch fixen)
- Desktop-spezifischer Vision-Prompt (Pixel-Koordinaten, keine CSS-Selektoren)
- Strukturierte Koordinaten-Rueckgabe (JSON mit Element-Name, Typ, x, y, w, h)
- Prompt-Engineering fuer qwen3-vl:32b mit Desktop-Screenshots
- Multi-Monitor-Support in der Vision-Analyse
- Window-Focusing per Vision + Click (statt PowerShell-Hacks)

### Erfolgskriterium
Cognithor macht einen Screenshot, erkennt UI-Elemente mit Koordinaten, klickt gezielt auf ein Element und verifiziert per Screenshot ob der Klick erfolgreich war.

---

## Sub-Projekt 2B: Agent Loop

**Status:** Offen
**Abhaengigkeit:** 2A

### Was gebaut wird
- Multi-Turn Screenshot→Decide→Act Schleife im PGE-Loop
- Scroll-Management (erkennen wann scrollen noetig, wie weit, Ende erkennen)
- Content-Extraction aus Screenshots (OCR-aehnlich via Vision-Model)
- State-Tracking ueber mehrere Iterationen (was wurde schon gesehen/geklickt)
- Abbruch-Bedingungen (Timeout, max Iterationen, User-Interrupt)
- Fortschritts-Reporting an den User waehrend der Ausfuehrung

### Erfolgskriterium
Cognithor oeffnet eine Anwendung, navigiert zu einem bestimmten Bereich, scrollt durch Inhalte und extrahiert Text aus dem was er sieht — ueber 10+ autonome Schritte hinweg.

---

## Sub-Projekt 2C: Planner Intelligence

**Status:** Offen
**Abhaengigkeit:** 2A + 2B

### Was gebaut wird
- Komplexe mehrstufige Aufgaben in Sub-Tasks zerlegen
- Datei-Erstellung mit extrahiertem Content (Zusammenfassungen, Tabellen)
- Dynamische Dateinamen (Datum, Variablen)
- Fehler-Recovery (Element nicht gefunden → alternativer Pfad)
- Kontext-Akkumulation (gesammelte Daten ueber Schritte hinweg merken)
- Abschluss-Reporting (Dateipfad, Zusammenfassung was gemacht wurde)

### Erfolgskriterium
Das vollstaendige Reddit-Szenario funktioniert: App oeffnen → suchen → 10 Posts scrollen → Zusammenfassungen erstellen → Datei speichern → User informieren.

---

## Technische Grundlagen (alle Sub-Projekte)

### Hardware
- NVIDIA RTX 5090 (32 GB VRAM)
- 4 Monitore (2560x1440 + 3x 1920x1080)
- Windows 11, 256 GB RAM

### Modelle
- Planner/Executor: qwen3.5:27b-16k
- Vision: qwen3-vl:32b (lokal via Ollama)
- Embedding: qwen3-embedding:0.6b

### Bestehende Infrastruktur (Phase 1)
- 6 Computer Use Tools: screenshot, click, type, hotkey, scroll, drag
- Sequentielle Ausfuehrung erzwungen (max_parallel=1)
- Clipboard-Paste fuer Texteingabe
- Multi-Monitor-Screenshots (combined oder einzeln)
- Verifikations-Screenshot nach erfolgreicher Aktion
- Anti-Double-Execution (REPLAN nach CU-Success blockiert)
- Sicherheit: Aktive Tools als YELLOW, pyautogui.FAILSAFE=True

### Key Files
- `src/jarvis/mcp/computer_use.py` — 6 Tools + Screenshot
- `src/jarvis/browser/vision.py` — VisionAnalyzer (API-Mismatch!)
- `src/jarvis/core/vision.py` — Backend-agnostische Vision-Messages
- `src/jarvis/core/unified_llm.py` — LLM-Client fuer Vision-Calls
- `src/jarvis/core/executor.py` — Sequentielle CU-Ausfuehrung
- `src/jarvis/core/planner.py` — System-Prompt mit CU-Instruktionen
- `src/jarvis/gateway/gateway.py` — Verifikation + REPLAN-Block
- `src/jarvis/gateway/phases/tools.py` — VisionAnalyzer-Erstellung
