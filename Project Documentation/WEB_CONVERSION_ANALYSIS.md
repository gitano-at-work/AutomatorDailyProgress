# LSKP Web Conversion — Feasibility Analysis

> **Status:** 📋 Shelved — Ready to execute when decided  
> **Created:** 2026-02-27  
> **Context:** Analysis of converting the desktop .exe app into a credit-based web SaaS

---

## The Problem This Solves

The current LSKP app is distributed as a standalone `.exe`. Users are hesitant to install it ("random exe from some random guy"), and monetization is nearly impossible with a desktop app. A web version solves both: **trust** (just use a website) and **revenue** (credit-based pay-per-use).

## Value Proposition

> "Why would someone use a web app to automate another web app?"

The value isn't about "accessing" the BKN portal — it's about **skipping 30-45 minutes of repetitive form-filling**.

### What the User Does Today (Without LSKP)

For each daily entry, they manually:
1. Open asndigital.bkn.go.id
2. Navigate through menus → Kinerja → SKP → Progress Harian
3. Click "Tambah Progress"
4. Pick date from datepicker
5. Type start time, end time
6. Select category from dropdown
7. Type description
8. Paste proof link
9. Select Rencana Aksi from dropdown
10. Submit
11. **Repeat for every time block, every day**

If they missed 3 days, that's easily **9-15 form submissions**, each taking 2-3 minutes = **30-45 minutes of clicking**.

### What the User Does With LSKP Web

1. Write their activities in a Google Doc (which many already do as personal notes)
2. Paste the Google Doc URL
3. Click Start
4. Enter 2FA code once
5. Done — **all entries filled in ~2 minutes**

### The Real Comparison

| Without LSKP | With LSKP |
| --- | --- |
| Fill forms one by one | Batch-fill everything at once |
| Navigate complex menus repeatedly | One-click automation |
| Remember exact format for each field | Write naturally in Google Doc |
| 30-45 min for backfill | 2 minutes total |
| Easy to forget/skip days | Catches up automatically |

> **Marketing angle:** Don't sell "we fill forms for you." Sell **"Never miss a daily report again. Write your notes, we handle the rest."** The pain point is compliance, not form-filling.

---

## Architecture

```
┌──────────────┐       ┌──────────────┐        ┌──────────────┐
│ User Browser │──────>│  Web App     │───────>│  Job Queue   │
│              │       │  (Frontend   │        │  (Redis/     │
│              │       │   + API)     │        │   BullMQ)    │
└──────────────┘       └──────────────┘        └──────┬───────┘
       ▲                      │                       │
       │                      ▼                       ▼
       │               ┌──────────────┐        ┌──────────────┐
       │               │  Database    │        │  Playwright  │
       └───────────────│  (Users,     │        │  Worker      │
        2FA relay      │   Credits,   │        │  (Your       │
                       │   Jobs)      │        │   existing   │
                       └──────────────┘        │   code)      │
                                               └──────┬───────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │  ASN Digital │
                                               │  Portal      │
                                               └──────────────┘
```

### 2FA Flow (Mandatory User Input)

This is the cleanest approach:

1. User clicks "Start Automation" on the web app
2. Server launches Playwright, opens BKN portal
3. Server submits username/password to SSO
4. BKN sends 2FA code to **user's phone/email** (this happens outside your system)
5. Your web app shows: *"Enter the 2FA code sent to your phone"*
6. User types code on **your site**
7. Server enters the code into the BKN SSO page
8. Login completes → automation runs → entries filled

The existing `browser_controller.py` already supports this — the `login(auth_code=None)` method has an `auth_code` parameter ready for exactly this scenario.

---

## Code Reusability

> See `CODE_REUSE_MAP.md` in this folder for the detailed file-by-file breakdown.

**Summary:** ~60% of the current codebase transfers directly to the web version. The core automation logic (parsing, filling, scanning) is cleanly separated from the GUI.

---

## Credit System

### Pricing Model

| Tier | Credits | Price | Per Entry |
| --- | --- | --- | --- |
| Free Trial | 5 | Rp 0 | Free |
| Starter | 30 | Rp 15,000 | Rp 500 |
| Monthly | 100 | Rp 35,000 | Rp 350 |
| Bulk | 300 | Rp 75,000 | Rp 250 |

### Rules

- **1 credit = 1 successfully submitted entry**
- Credits deducted **only after confirmed submission** (not on attempt)
- Failed entries = no charge
- Preview shown first: *"Found 7 entries to fill. This will use 7 credits. Proceed?"*

### Server Cost vs Revenue

Each automation run uses ~200-400MB RAM for a Chromium instance, running 2-5 minutes.

| VPS RAM | Max Concurrent Jobs | Users/Day | Revenue Potential |
| --- | --- | --- | --- |
| 2 GB | 2-3 | ~50 | ~Rp 125K/day |
| 4 GB | 5-8 | ~150 | ~Rp 375K/day |
| 8 GB | 10-15 | ~400 | ~Rp 1M/day |

---

## Tech Stack

| Layer | Technology | Why |
| --- | --- | --- |
| Frontend | Next.js | SSR for SEO, React ecosystem, good auth libraries |
| Backend API | Next.js API Routes or Express | Same language as frontend, keep it simple |
| Database | PostgreSQL | Users, credits, job history — reliable and free |
| Job Queue | BullMQ + Redis | Manages automation jobs, retries, concurrency limits |
| Automation | Playwright (Python) | Existing working code — runs as a background worker |
| Auth | NextAuth.js | Google/email login, session management |
| Payments | Midtrans or Xendit | Indonesian payment gateways (credit card + e-wallet) |

---

## Risks

### 🔴 High Risk

- **BKN portal changes** — If they update their website selectors, automation breaks. Paying users mean higher pressure to fix fast.
- **Credential storage** — Storing government portal passwords is a serious security responsibility. Requires proper encryption and security practices.

### 🟡 Medium Risk

- **IP blocking** — Multiple logins from one server IP could trigger BKN's security. May need IP rotation or request throttling.
- **Legal/ToS** — Automated access to government portals may violate their Terms of Service. Research before going public.

### 🟢 Low Risk

- **Server costs** — VPS can handle initial users easily. Credit revenue covers costs.
- **Code migration** — Core logic is well-structured and modular.

---

## Build Estimate

| Phase | What | Effort |
| --- | --- | --- |
| Phase 1 | Web frontend (auth, dashboard, credit display) | 2-3 weeks |
| Phase 2 | Backend API + job queue + worker integration | 2-3 weeks |
| Phase 3 | Payment integration + credit system | 1-2 weeks |
| Phase 4 | Testing, polish, security hardening | 1-2 weeks |
| **Total** | | **6-10 weeks** |

> See `WEB_CONVERSION_PLAN.md` in this folder for the detailed phase-by-phase execution plan.
