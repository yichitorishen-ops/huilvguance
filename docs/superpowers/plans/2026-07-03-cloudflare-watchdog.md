# Cloudflare Watchdog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Cloudflare Worker Cron watchdog that triggers the existing GitHub Pages data workflow when GitHub's own scheduled events are missed.

**Architecture:** The Worker runs every 10 minutes on off-hour minutes and checks Beijing time against the existing `00:00`, `06:00`, `13:00`, and `18:00` capture windows. If the current time is inside a `-2h` to `+2h` window, it calls GitHub `workflow_dispatch` with `collect=true` and the matching `scheduled_hour`; the repository workflow remains responsible for fetching data, preserving history, building the static site, and deploying Pages.

**Tech Stack:** Cloudflare Workers Cron Triggers, GitHub Actions workflow dispatch API, existing Python collection workflow, Python unittest coverage.

---

### Task 1: Make External Workflow Dispatch Idempotent

**Files:**
- Modify: `scripts/collect_once.py`
- Test: `tests/test_scripts.py`

- [ ] **Step 1: Write the failing test**

Add a test that verifies the workflow command uses `skip_existing=True` when `--scheduled-hour` is passed, because Cloudflare will call the dispatch endpoint repeatedly during one capture window.

- [ ] **Step 2: Run the test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_scripts -v`

- [ ] **Step 3: Implement the minimal script change**

Set `skip_existing=True` for both `--schedule-cron` and `--scheduled-hour`, while leaving normal catch-up behavior unchanged.

- [ ] **Step 4: Verify the test passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_scripts -v`

### Task 2: Add Worker Source and Configuration

**Files:**
- Create: `cloudflare/huilvguance-watchdog/wrangler.toml`
- Create: `cloudflare/huilvguance-watchdog/src/index.js`
- Create: `tests/test_cloudflare_worker.py`

- [ ] **Step 1: Write failing tests**

Assert that the Worker config uses `7,17,27,37,47,57 * * * *`, that the Worker dispatches to `repos/yichitorishen-ops/huilvguance/actions/workflows/pages.yml/dispatches`, and that it sends `collect=true`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_cloudflare_worker -v`

- [ ] **Step 3: Implement Worker files**

Create a Worker with a `scheduled()` handler and an HTTP `fetch()` dry-run endpoint. The Worker reads `GITHUB_TOKEN` from Cloudflare secrets and posts to GitHub only inside active capture windows.

- [ ] **Step 4: Verify Worker tests pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_cloudflare_worker -v`

### Task 3: Verify, Deploy, and Smoke Test

**Files:**
- No further repo files required.

- [ ] **Step 1: Run full local verification**

Run: `.\.venv\Scripts\python.exe -m unittest discover -v`

- [ ] **Step 2: Deploy Worker**

Use `CLOUDFLARE_API_TOKEN` and account id `da5447a259dab3a8964ef0b06c91f2c3` with Wrangler. Store the GitHub workflow token as a Cloudflare Worker secret named `GITHUB_TOKEN`.

- [ ] **Step 3: Smoke test**

Call the deployed Worker's HTTP dry-run endpoint and verify it reports the active or inactive slot decision without exposing secrets.

- [ ] **Step 4: Commit and push repo changes**

Push the Worker source, config, tests, and idempotency fix to `main`.
