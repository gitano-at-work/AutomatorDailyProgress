# LSKP Web Conversion — Execution Plan

> **Status:** 📋 Shelved — Ready to execute when decided  
> **Created:** 2026-02-27  
> **Prerequisite:** Read `WEB_CONVERSION_ANALYSIS.md` first for context

---

## Pre-Build Checklist

Before writing any code, these decisions need to be made:

- [ ] **Legal check** — Review BKN portal ToS for automated access restrictions
- [ ] **Demand validation** — Consider a landing page + waitlist to gauge interest before investing 6-10 weeks
- [ ] **Domain & branding** — Pick a domain name and product name for the web version
- [ ] **VPS specs** — Confirm your VPS has at least 2GB RAM with room to grow
- [ ] **Payment gateway** — Create a Midtrans or Xendit merchant account

---

## Phase 1: Foundation (2-3 weeks)

### Goal: User can sign up, log in, see a dashboard

#### Tasks

- [ ] Initialize Next.js project
- [ ] Set up PostgreSQL database with initial schema:
  - `users` table (id, email, name, credits, created_at)
  - `credentials` table (id, user_id, bkn_username, bkn_password_encrypted)
  - `jobs` table (id, user_id, status, entries_found, entries_filled, created_at)
  - `credit_transactions` table (id, user_id, amount, type, job_id, created_at)
- [ ] Implement auth (NextAuth.js — Google + email login)
- [ ] Build dashboard page:
  - Credit balance display
  - Job history table
  - "Start New Automation" button
- [ ] Build settings page:
  - BKN credentials input (encrypted storage)
  - Google Doc URL input
- [ ] Deploy to VPS with basic Nginx + PM2 setup

### Decisions Needed at This Phase

- Which auth providers? (Google only? Email + password? Both?)
- Free trial: 5 credits on signup, or require email verification first?

---

## Phase 2: Automation Backend (2-3 weeks)

### Goal: User can submit a job and entries get filled

#### Tasks

- [ ] Set up Redis + BullMQ job queue
- [ ] Create Python worker service that:
  - Picks up jobs from Redis queue
  - Runs existing Playwright automation code
  - Reports progress back via Redis pub/sub or WebSocket
- [ ] Build the "job submission" API:
  - Parse Google Doc → preview entries for user
  - User confirms → queue job
  - Return job status via polling or WebSocket
- [ ] Adapt existing code for server-side:
  - `doc_parser.py` → expose as API endpoint or call from worker
  - `browser_controller.py` → remove desktop-specific code, add auth_code relay
  - `form_filler.py` → swap GUI logger for server logger
  - `calendar_scanner.py` → same logger swap
- [ ] Build 2FA relay flow:
  - Worker pauses when 2FA is needed
  - API notifies frontend: "Enter 2FA code"
  - Frontend shows input field
  - User submits code → API relays to worker → worker enters code

### Key Technical Challenge

The Python worker and Node.js API need to communicate:
- **Option A:** Redis pub/sub (simplest — worker publishes events, API subscribes)
- **Option B:** REST API on the Python worker (more complex but more control)
- **Recommended:** Option A for v1

---

## Phase 3: Payments (1-2 weeks)

### Goal: User can buy credits

#### Tasks

- [ ] Integrate Midtrans or Xendit payment gateway
- [ ] Build "Buy Credits" page with tier selection
- [ ] Implement payment webhook handler:
  - Verify payment signature
  - Add credits to user account
  - Record transaction
- [ ] Add credit deduction logic:
  - Preview: "This will use X credits"
  - Deduct after each successful entry (not upfront)
  - Insufficient credits → block job start
- [ ] Add simple admin dashboard (for you):
  - Total users, revenue, jobs run
  - Manual credit adjustment if needed

---

## Phase 4: Polish & Security (1-2 weeks)

### Goal: Production-ready

#### Tasks

- [ ] Security hardening:
  - Encrypt stored BKN credentials (AES-256 or similar)
  - Rate limiting on login and API endpoints
  - HTTPS everywhere
  - Input sanitization
- [ ] Error handling:
  - Retry logic for flaky BKN portal responses
  - Refund credits on server-side failures
  - Clear error messages for users
- [ ] Monitoring:
  - Job success/failure rates
  - Server resource usage (RAM, CPU per worker)
  - Alert on high failure rates (BKN portal might have changed)
- [ ] Landing page:
  - Clear value proposition
  - How it works (3-step visual)
  - Pricing tiers
  - FAQ addressing security concerns
- [ ] Final testing round

---

## Post-Launch

- [ ] Monitor BKN portal for selector changes (weekly manual check or automated test)
- [ ] Collect user feedback for v2 features
- [ ] Consider: browser extension as alternative to server-side automation (lower cost, user's own credentials stay local)
