# CAPTCHA Solver — Design Spec

**Spec v1.0** — 30.03.2026
**Status:** Approved Design
**Ziel:** Cognithor kann CAPTCHAs auf Webseiten erkennen und loesen — rein lokal via Vision-LLM, ohne externe Solving-Services.

---

## 1. Motivation

Cognithor hat Browser-Automatisierung (Playwright, 13 Tools), aber null CAPTCHA-Handling.
Wenn bei Web-Recherche oder Formular-Automatisierung ein CAPTCHA auftaucht, scheitert der
Task. Dieses Feature schliesst diese Luecke fuer zwei Use-Cases:

1. **Web-Automation** — CAPTCHAs als Hindernis bei Recherche/Formular-Tasks ueberwinden
2. **Pentesting/Security-Audit** — Bot-Schutz auf autorisierten Sites testen

---

## 2. Unterstuetzte CAPTCHA-Typen

| Typ | Erkennung | Solve-Strategie |
|-----|-----------|-----------------|
| **Text-CAPTCHA** | `<img>` neben Text-Input | Screenshot → Vision-LLM → Text extrahieren → Input fuellen |
| **reCAPTCHA v2 Checkbox** | `#g-recaptcha`, `[data-sitekey]` | Klick auf Checkbox, bei Image-Challenge: Screenshot → Vision-LLM |
| **reCAPTCHA v2 Image Grid** | iframe mit Bild-Grid | Screenshot → Vision-LLM "Welche Bilder zeigen X?" → Klick-Koordinaten |
| **reCAPTCHA v3** | `grecaptcha.execute` im DOM | Unsichtbar, score-basiert. Stealth-Mode + normales Browser-Verhalten reicht oft |
| **hCaptcha** | `.h-captcha`, `[data-sitekey]` | Aehnlich wie reCAPTCHA v2: Checkbox → ggf. Image-Challenge |
| **Cloudflare Turnstile** | `cf-turnstile`, `[data-sitekey]` | Meist automatisch mit Stealth. Bei Challenge: Screenshot → Vision-LLM |
| **FunCaptcha/Arkose** | `#FunCaptcha`, `arkoselabs` | Screenshot → Vision-LLM fuer Puzzle-Erkennung |

---

## 3. Architektur

```
Browser navigiert zu Seite
         |
         v
  ┌──────────────┐
  │   DETECTOR    │  JS-Scan: Selektoren, iframes, sitekeys
  │  detector.py  │
  └──────┬───────┘
         | CaptchaChallenge
         v
  ┌──────────────┐
  │  CLASSIFIER   │  DOM-Analyse → CaptchaType enum
  │ classifier.py │
  └──────┬───────┘
         | CaptchaType + metadata
         v
  ┌──────────────┐
  │   SOLVER      │  Orchestrator: Strategie waehlen → ausfuehren → verifizieren
  │  solver.py    │
  └──────┬───────┘
         |
    ┌────┴─────┐
    v          v
┌────────┐ ┌────────┐
│Strategy│ │Strategy│  Pro Typ: screenshot → Vision-LLM → parse → act
│  Text  │ │ Image  │
│        │ │  Grid  │
└────┬───┘ └────┬───┘
     |          |
     v          v
  ┌──────────────┐
  │   INJECTOR    │  Token/Antwort in Seite einfuegen, Submit
  │ (in solver)   │
  └──────┬───────┘
         |
         v
  ┌──────────────┐
  │   VERIFY      │  Seite hat sich geaendert? CAPTCHA weg? Fehler-Meldung?
  │ (in solver)   │
  └──────┬───────┘
         |
    ┌────┴─────┐
    v          v
  Erfolg    Retry (max 3)
    |          |
    v          v
  TacticalMemory: Ergebnis speichern (Typ, Modell, Erfolg, Dauer)
```

---

## 4. Neue Dateien

```
src/jarvis/browser/captcha/
├── __init__.py           # Package exports
├── models.py             # CaptchaType enum, CaptchaChallenge, SolveResult dataclasses
├── detector.py           # JS-basierte CAPTCHA-Erkennung auf Playwright-Page
├── classifier.py         # Typ-Klassifizierung aus Detector-Output
├── solver.py             # Orchestrator: detect → classify → solve → inject → verify → learn
├── strategies.py         # Solve-Strategien pro Typ (Vision-LLM Prompts + Aktionen)
└── stealth.py            # Basis-Stealth: Launch-Args + JS-Injection
```

---

## 5. Datenmodelle (`models.py`)

```python
class CaptchaType(StrEnum):
    TEXT = "text"
    RECAPTCHA_V2_CHECKBOX = "recaptcha_v2_checkbox"
    RECAPTCHA_V2_IMAGE = "recaptcha_v2_image"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    FUNCAPTCHA = "funcaptcha"
    UNKNOWN = "unknown"

@dataclass
class CaptchaChallenge:
    captcha_type: CaptchaType
    selector: str              # CSS-Selektor des CAPTCHA-Elements
    sitekey: str = ""          # data-sitekey wenn vorhanden
    iframe_url: str = ""       # URL des CAPTCHA-iframes
    page_url: str = ""         # URL der aktuellen Seite
    screenshot_b64: str = ""   # Base64-PNG des CAPTCHA-Bereichs

@dataclass
class SolveResult:
    success: bool
    captcha_type: CaptchaType
    model_used: str            # z.B. "minicpm-v4.5" oder "qwen3-vl:32b"
    attempts: int
    duration_ms: int
    answer: str = ""           # Was das Vision-LLM geantwortet hat
    error: str = ""            # Fehler-Details bei Misserfolg
```

---

## 6. Detector (`detector.py`)

JavaScript das auf der Playwright-Page ausgefuehrt wird:

```javascript
// Sucht nach bekannten CAPTCHA-Selektoren
const captchas = [];

// reCAPTCHA v2
const recaptcha = document.querySelector('[data-sitekey].g-recaptcha, #g-recaptcha');
if (recaptcha) captchas.push({type: 'recaptcha_v2', selector: '...', sitekey: '...'});

// reCAPTCHA v3 (unsichtbar)
if (typeof grecaptcha !== 'undefined' && !recaptcha) captchas.push({type: 'recaptcha_v3'});

// hCaptcha
const hcaptcha = document.querySelector('.h-captcha, [data-sitekey][data-hcaptcha]');

// Cloudflare Turnstile
const turnstile = document.querySelector('.cf-turnstile, [data-sitekey][data-callback]');

// FunCaptcha / Arkose
const funcaptcha = document.querySelector('#FunCaptcha, [data-arkoselabs]');

// Text-CAPTCHA (heuristisch: img + input in der Naehe)
// ... Heuristik basierend auf img neben input[type=text]

return captchas;
```

---

## 7. Solver Strategien (`strategies.py`)

### 7.1 Text-CAPTCHA

```
1. Screenshot des CAPTCHA-Bildes (element.screenshot())
2. Vision-LLM (minicpm-v4.5 zuerst):
   Prompt: "Lies den verzerrten Text in diesem CAPTCHA-Bild.
            Antworte NUR mit dem Text, keine Erklaerung."
3. Antwort in das Text-Input neben dem CAPTCHA-Bild einfuegen
4. Formular absenden
```

### 7.2 reCAPTCHA v2 Checkbox

```
1. Klick auf die Checkbox (#recaptcha-anchor)
2. Warte 2-3 Sekunden
3. Pruefen: Checkbox hat Haekchen? → Fertig
4. Wenn Image-Challenge erscheint → delegiere an Image-Grid-Strategie
```

### 7.3 reCAPTCHA v2 Image Grid

```
1. Screenshot des Challenge-iframes
2. Challenge-Text extrahieren (z.B. "Waehle alle Bilder mit Ampeln")
3. Vision-LLM (qwen3-vl:32b — komplexer Task):
   Prompt: "Dieses Bild zeigt ein 3x3 oder 4x4 Grid.
            Die Aufgabe ist: '{challenge_text}'.
            Antworte mit den Positionen der richtigen Bilder
            als Liste: [row,col] mit 0-basiertem Index.
            Format: [[0,1],[1,2],[2,0]]"
4. Parse Koordinaten → Klick auf die entsprechenden Grid-Zellen
5. "Verify" Button klicken
6. Pruefen ob neue Challenge oder Erfolg
```

### 7.4 reCAPTCHA v3 (Unsichtbar)

```
1. Stealth-Mode muss aktiv sein (sonst sofort Score 0)
2. Kein direkter Solve noetig — Score wird automatisch berechnet
3. Wenn Score zu niedrig → Fallback nicht moeglich (kein externer Service)
4. Logging: "reCAPTCHA v3 erkannt, Stealth-Mode aktiv, Score-basiert"
```

### 7.5 hCaptcha

```
1. Klick auf Checkbox
2. Wenn Image-Challenge: gleiche Strategie wie reCAPTCHA v2 Image Grid
3. hCaptcha hat aehnliche Image-Grid-Challenges
```

### 7.6 Cloudflare Turnstile

```
1. Stealth-Mode + warten (Turnstile loest sich oft automatisch)
2. Wenn interaktive Challenge: Screenshot → Vision-LLM
3. Turnstile-Token wird automatisch in hidden input gesetzt
```

### 7.7 FunCaptcha/Arkose

```
1. Screenshot des Puzzles
2. Vision-LLM: "Dieses Bild zeigt ein Puzzle/Drehspiel.
                Beschreibe was zu tun ist und welche Aktion noetig ist."
3. Versuche basierend auf LLM-Antwort die Interaktion
4. Niedrigste erwartete Erfolgsrate — dokumentieren
```

---

## 8. Dynamische Modellwahl

```python
# Modell-Auswahl basierend auf CAPTCHA-Komplexitaet
MODEL_PREFERENCE = {
    CaptchaType.TEXT: "minicpm-v4.5",              # Einfach, parallel-faehig
    CaptchaType.RECAPTCHA_V2_CHECKBOX: None,       # Kein Vision noetig (nur Klick)
    CaptchaType.RECAPTCHA_V2_IMAGE: "qwen3-vl:32b",  # Komplex, braucht starkes Modell
    CaptchaType.RECAPTCHA_V3: None,                # Kein Vision noetig (Stealth)
    CaptchaType.HCAPTCHA: "qwen3-vl:32b",         # Image-Challenges sind komplex
    CaptchaType.TURNSTILE: "minicpm-v4.5",         # Meist einfach wenn ueberhaupt
    CaptchaType.FUNCAPTCHA: "qwen3-vl:32b",        # Puzzle, braucht starkes Modell
}
```

TacticalMemory ueberschreibt diese Defaults nach genuegend Erfahrungsdaten
(z.B. wenn minicpm bei Turnstile immer scheitert → automatisch qwen3-vl).

---

## 9. Stealth (`stealth.py`)

Basis-Stealth bei jedem Playwright-Launch:

```python
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
]

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => false});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['de-DE', 'de', 'en-US', 'en']});
window.chrome = {runtime: {}};
"""

REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

DEFAULT_VIEWPORT = {"width": 1280, "height": 720}
```

Stealth-JS wird via `page.add_init_script()` bei jeder neuen Seite injiziert.

---

## 10. Integration in bestehende Module

### 10.1 Browser Agent — Auto-Detect

In `browser/agent.py`, nach jeder Navigation:

```python
# Nach page.goto() und Cookie-Banner-Dismiss:
if self._captcha_config.enabled:
    challenge = await detect_captcha(page)
    if challenge:
        result = await self._captcha_solver.solve(page, challenge)
        log.info("captcha_auto_solved", type=challenge.captcha_type, success=result.success)
```

### 10.2 MCP Tool

```python
# browser_solve_captcha — manuell aufrufbar
async def browser_solve_captcha(max_retries: int = 3) -> str:
    """Erkennt und loest ein CAPTCHA auf der aktuellen Browser-Seite."""
```

### 10.3 Gatekeeper

- `browser_solve_captcha` → **ORANGE** (erfordert User-Genehmigung)

### 10.4 Config

```yaml
captcha:
  enabled: false                    # Opt-in
  max_retries: 3
  stealth_enabled: true
  auto_solve: true                  # Automatisch bei Navigation loesen
  preferred_simple_model: "openbmb/minicpm-v4.5:latest"
  preferred_complex_model: "qwen3-vl:32b"
  solve_timeout_seconds: 30
```

### 10.5 TacticalMemory

Jeder Solve-Versuch wird gespeichert:
```python
tactical.record_outcome(
    tool_name="browser_solve_captcha",
    params={"type": captcha_type, "model": model_used, "domain": domain},
    success=result.success,
    duration_ms=result.duration_ms,
)
```

### 10.6 Skill

`~/.cognithor/skills/generated/captcha_solver.md` — beschreibt wann und wie
der Solver eingesetzt wird, damit der Planner ihn korrekt aufruft.

---

## 11. Sicherheit

| Massnahme | Beschreibung |
|-----------|-------------|
| **Opt-in** | `captcha.enabled: false` default |
| **Gatekeeper ORANGE** | User muss CAPTCHA-Solving explizit genehmigen |
| **ATL-Blockade** | Risk ceiling YELLOW verhindert autonomes CAPTCHA-Solving |
| **Audit Trail** | Jeder Solve-Versuch geloggt (Typ, URL, Ergebnis) |
| **Keine externen Services** | Kein Datentransfer zu Drittanbietern |
| **Stealth transparent** | Stealth-Massnahmen sind konfigurierbar und deaktivierbar |

---

## 12. Tests

### Unit Tests (~20)
- Detector: Mock-HTML mit verschiedenen CAPTCHA-Typen → korrekte Erkennung
- Classifier: DOM-Snapshots → korrekte CaptchaType-Zuordnung
- Strategies: Mock-Vision-Responses → korrekte Koordinaten/Text-Extraktion
- Solver: Mock-Ablaeufe → Retry-Logik, Timeout, Error-Handling
- Stealth: Launch-Args korrekt, JS-Injection vorhanden
- Models: Dataclass-Serialisierung

### Integration Tests (~5)
- Lokale Test-HTML-Seite mit simuliertem CAPTCHA-Element
- Detect → Classify → Solve mit Mock-Vision → Inject → Verify
- Stealth-Args korrekt an Playwright uebergeben
- TacticalMemory-Eintrag nach Solve

### Dry-Run Tests (~3, manuell)
- Google reCAPTCHA v2 Demo-Seite
- hCaptcha Demo-Seite
- Cloudflare Turnstile Demo-Seite
- Nur mit `--captcha-live` Flag, nicht in CI

---

## 13. Erwartete Solve-Raten (ehrliche Einschaetzung)

| Typ | Erwartete Rate | Begruendung |
|-----|---------------|-------------|
| Text-CAPTCHA | 60-80% | Vision-LLMs koennen verzerrten Text oft lesen |
| reCAPTCHA v2 Checkbox | 70-90% | Checkbox-Klick + Stealth reicht oft |
| reCAPTCHA v2 Image Grid | 10-30% | Multi-Image-Klassifikation ist extrem schwer fuer LLMs |
| reCAPTCHA v3 | 50-70% | Abhaengig von Stealth-Qualitaet und Seitenverhalten |
| hCaptcha Image | 10-25% | Aehnlich schwer wie reCAPTCHA v2 Images |
| Turnstile | 60-80% | Oft automatisch mit Stealth loesbar |
| FunCaptcha | 5-15% | Puzzle-Erkennung ist fuer aktuelle LLMs sehr schwer |

Diese Raten sind der **Startpunkt**. Durch TacticalMemory-Feedback und
iterative Prompt-Verbesserung koennen sie sich ueber Zeit verbessern.

---

*Spec v1.0 — CAPTCHA Solver — 30.03.2026*
