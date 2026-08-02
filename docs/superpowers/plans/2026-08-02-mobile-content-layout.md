# Mobile Content Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the requested mobile screens readable and non-scrollable horizontally while preserving desktop behavior and existing interactions.

**Architecture:** Keep desktop Element Plus tables and the current mobile navigation behavior. Add mobile-only card lists for Records, Plans, and Reminders, then use a scoped mobile CSS override block for cards, links, segmented controls, colors, and drawer sizing. Validate source contracts, build output, and live viewport widths.

**Tech Stack:** Vue 3, Vite, Element Plus, plain CSS, Node `node:test`.

## Global Constraints

- Mobile breakpoint remains `max-width: 760px`.
- Mobile drawer width must not exceed `50vw`.
- Desktop table markup remains available above the mobile breakpoint.
- Do not change backend APIs, persistence, or route behavior.
- Mobile pages must not create page-level horizontal overflow.

---

### Task 1: Add mobile card structures for list pages

**Files:**
- Modify: `frontend/src/pages/Records.vue`
- Modify: `frontend/src/pages/Plans.vue`
- Modify: `frontend/src/pages/Reminders.vue`
- Test: `frontend/src/pages/mobileContentLayoutContract.test.js`

**Interfaces:**
- Consumes: existing `rows` refs and `openEdit`, `remove`, `action` handlers.
- Produces: `.desktop-table` and `.mobile-card-list` hooks with the same data and actions.

- [ ] **Step 1: Write the failing source contract test**

  Assert that each page contains a desktop table hook, a mobile card list hook, and the mobile card classes for the page-specific primary fields and actions.

- [ ] **Step 2: Run the focused test and verify it fails**

  Run `npm test -- --test-name-pattern="mobile content"` from `frontend/`.
  Expected: FAIL because the new mobile hooks do not exist yet.

- [ ] **Step 3: Add mobile markup without changing data logic**

  Keep each existing `el-table` inside `.desktop-table`. Add a `.mobile-card-list` sibling using the same `rows` array. Records show date, hours, title, truncated content, tags, edit/delete; Plans show title, date range, priority, status, edit/delete; Reminders show title, rule, optional content, status, and the existing action set.

- [ ] **Step 4: Run the focused test and verify it passes**

  Run `npm test -- --test-name-pattern="mobile content"` from `frontend/`.
  Expected: PASS.

- [ ] **Step 5: Commit**

  Run `git add frontend/src/pages frontend/src/pages/mobileContentLayoutContract.test.js && git commit -m "feat: add mobile card lists"`.

### Task 2: Refine mobile navigation, page surfaces, links, and accounting controls

**Files:**
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/layouts/mobileStyleContract.test.js`

**Interfaces:**
- Consumes: existing theme variables, `.mobile-nav-panel`, `.link-grid`, accounting class hooks, and Element Plus control classes.
- Produces: mobile-only rules for no horizontal overflow, single-column links, centered segmented labels, and drawer width.

- [ ] **Step 1: Extend the style contract with failing assertions**

  Add assertions for `width: min(300px, 50vw)`, `.desktop-table`, `.mobile-card-list`, `.link-grid` single-column behavior, and centered radio-button content.

- [ ] **Step 2: Run the style contract and verify the new assertions fail**

  Run `npm test -- --test-name-pattern="mobile styles"` from `frontend/`.
  Expected: FAIL for the new rules.

- [ ] **Step 3: Add the mobile override rules**

  In the existing mobile block, hide `.desktop-table`, show `.mobile-card-list`, set `.mobile-nav-panel { width: min(300px, 50vw); }`, use theme-aware topbar tint variables, set link categories to full-width wrapping controls, set `.link-grid { grid-template-columns: 1fr; }`, and make card content `min-width: 0`. Set radio and segmented internals to flex-centered text and full-width period controls on accounting.

- [ ] **Step 4: Run the style contract and full frontend tests**

  Run `npm test` from `frontend/`.
  Expected: all tests PASS.

- [ ] **Step 5: Commit**

  Run `git add frontend/src/styles.css frontend/src/layouts/mobileStyleContract.test.js && git commit -m "feat: refine mobile content surfaces"`.

### Task 3: Verify build and live mobile behavior

**Files:**
- No source changes expected.

- [ ] **Step 1: Run source and build verification**

  Run `npm test`, `npm run build`, and `git diff --check` from `frontend/`/repo root.
  Expected: tests pass, build exits 0, and diff check is clean.

- [ ] **Step 2: Inspect the live app at mobile widths**

  Use the in-app browser at 390×844 and 768×900. Check the drawer width, topbar visual hierarchy, Records/Plans/Reminders card lists, Links single-column layout, Accounting control alignment, and `document.documentElement.scrollWidth === document.documentElement.clientWidth`.

- [ ] **Step 3: Commit any verification-only fixes if needed**

  If the browser exposes a concrete layout regression, add the smallest source/test fix, rerun the full verification commands, and commit it with a focused message.
