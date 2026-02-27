# LSKP - Task List

> Last updated: 2026-02-27

## Completed
- [x] Core GUI with Tkinter (login form, log display, settings)
- [x] Google Doc parser (Indonesian date formats, time ranges, categories)
- [x] Playwright browser automation (login, 2FA pause, dashboard detection)
- [x] Form filling automation (date, time, category, description, proof link)
- [x] Calendar scanning (detect existing entries to avoid duplicates)
- [x] Auto-update system (check GitHub releases, download, apply on restart)
- [x] Build pipeline (`build.bat` → PyInstaller → standalone `.exe`)
- [x] Dev launcher (`run.bat` → venv setup → run from source)
- [x] First-time setup screen (browser download flow)
- [x] Config persistence (`config.json`)
- [x] Headless mode support
- [x] Completion mode options

## Known Issues / Tech Debt
- [ ] Password stored in plain text in `config.json` (mitigated: file is gitignored)
- [ ] `calendar_dump.html` and `doc_dump.txt` are debug artifacts left in project root
- [ ] `test_svg.py` imports `svglib` and `reportlab` which are not in `requirements.txt`

## Future Ideas
- [ ] Encrypt credentials in config
- [ ] Multiple user profiles
- [ ] Windows Task Scheduler integration for auto-run
- [ ] Better error recovery on network failures

## 📋 Shelved: Web Conversion (Credit-Based SaaS)

> Full analysis and execution plan documented separately. Start here when ready:

- `WEB_CONVERSION_ANALYSIS.md` — Feasibility, value proposition, risks, pricing
- `WEB_CONVERSION_PLAN.md` — Phase-by-phase execution checklist
- `CODE_REUSE_MAP.md` — File-by-file guide on what transfers to the web version
