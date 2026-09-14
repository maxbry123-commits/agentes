# UI Preview and Redaction Guide

Use this guide to capture and share a **redacted** screenshot of the Security AI Agent web UI.

## What to Capture
- Page: main scan dashboard
- Elements: scan form, live log window, status badges, and report list panel
- Theme: default dark terminal style (helps legibility)

## Redaction Steps
1) Run a scan against a non-sensitive target (e.g., example.com) with PoC-only mode.
2) After logs populate, take a screenshot (PNG) of the dashboard.
3) Redact all target/domain/hostnames and any IPs in the log pane and report list.
4) Save as `ui/preview.png` in this repo.

## Notes for Sharing
- Keep resolution ~1280x720 for readability in the README.
- Avoid including timestamps or operator usernames if not needed.
- Confirm no customer or confidential data remains after redaction.

## Where It Shows Up
- The public README links to `ui/preview.png` for prospects to see the UI layout.
