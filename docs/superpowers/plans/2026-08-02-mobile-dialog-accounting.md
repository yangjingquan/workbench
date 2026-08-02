# Mobile Dialog and Accounting Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Center mobile dialogs and replace the two horizontally scrolling accounting tables with responsive mobile cards.

**Architecture:** Keep the existing desktop Element Plus tables and all business handlers. Add mobile-only accounting card lists sourced from the same `summary.by_category` and `entries` refs, then add one global mobile dialog layout rule and contract tests for the new hooks.

**Tech Stack:** Vue 3, Element Plus, plain CSS, Node `node:test`, Vite.

## Global Constraints

- Mobile breakpoint remains `max-width: 760px`.
- Desktop accounting tables must remain unchanged and visible above the mobile breakpoint.
- Mobile dialogs must use `calc(100vh - 32px)` as the maximum outer height.
- No API, persistence, route, or permission changes.

---

### Task 1: Add mobile accounting cards

**Files:**
- Modify: `frontend/src/pages/Accounting.vue`
- Create: `frontend/src/layouts/mobileAccountingContract.test.js`

**Interfaces:**
- Consumes: `summary.by_category`, `entries`, `formatMoney`, `removeEntry` and existing type color classes.
- Produces: `.desktop-accounting-table`, `.mobile-accounting-list`, `.mobile-category-card`, and `.mobile-entry-card` hooks.

- [ ] **Step 1: Write the failing source contract test**

  Read `Accounting.vue` and assert that it exposes desktop table hooks, both mobile list hooks, the category and entry card classes, and the existing delete handler.

- [ ] **Step 2: Run the focused test and verify it fails**

  Run `node --test src/layouts/mobileAccountingContract.test.js` from `frontend/`.
  Expected: FAIL because the new mobile hooks are absent.

- [ ] **Step 3: Add the mobile card markup**

  Add `.desktop-accounting-table` around each existing table. Add a category card list after the first table and an entry card list after the second table. Use the existing values and `@click="removeEntry(item.id)"` for deletion; do not add new state or API calls.

- [ ] **Step 4: Run the focused test and verify it passes**

  Run `node --test src/layouts/mobileAccountingContract.test.js` from `frontend/`.
  Expected: PASS.

- [ ] **Step 5: Commit**

  Run `git add frontend/src/pages/Accounting.vue frontend/src/layouts/mobileAccountingContract.test.js && git commit -m "feat: add mobile accounting cards"`.

### Task 2: Center mobile dialogs and style accounting cards

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/layouts/mobileStyleContract.test.js`

**Interfaces:**
- Consumes: existing mobile breakpoint, Element Plus dialog classes, accounting card hooks, and theme variables.
- Produces: centered dialog overlay, bounded dialog body, hidden mobile tables, visible accounting cards, and no horizontal overflow in accounting panels.

- [ ] **Step 1: Extend the style contract with failing assertions**

  Assert the presence of mobile `.el-overlay-dialog` flex alignment, bounded `.el-dialog` height, `.desktop-accounting-table` hidden behavior, and `.mobile-accounting-list` visible behavior.

- [ ] **Step 2: Run the style test and verify the new assertions fail**

  Run `node --test src/layouts/mobileStyleContract.test.js` from `frontend/`.
  Expected: FAIL for the new rules.

- [ ] **Step 3: Add mobile styles**

  In the final mobile override block, set `.el-overlay-dialog` to centered flex layout with 16px padding, set `.el-dialog` max height and zero vertical margin, and make `.el-dialog__body` the scroll region. Hide the two accounting desktop table wrappers, show the mobile lists, style cards with the existing surface/line/shadow variables, and set accounting panels to `overflow-x: hidden`.

- [ ] **Step 4: Run all frontend tests and build**

  Run `npm test`, `npm run build`, and `git diff --check`.
  Expected: all tests pass, Vite exits 0, and the diff check is clean.

- [ ] **Step 5: Commit**

  Run `git add frontend/src/styles.css frontend/src/layouts/mobileStyleContract.test.js && git commit -m "feat: center mobile dialogs"`.

### Task 3: Verify live mobile behavior

**Files:**
- No source changes expected unless verification finds a concrete regression.

- [ ] **Step 1: Open the authenticated app at 390×844**

  Visit Records, Plans, Reminders, Todos, Links, and Accounting. Open one target dialog from each relevant page and inspect its bounding rectangle; verify its center is within the viewport and its body can scroll when needed.

- [ ] **Step 2: Verify accounting overflow and desktop preservation**

  On Accounting, verify the two `.mobile-accounting-list` containers are visible, `.desktop-accounting-table` containers are hidden, page `scrollWidth === clientWidth`, and no accounting panel has a horizontal scrollbar.

- [ ] **Step 3: Run final verification and commit any scoped fix**

  Rerun `npm test`, `npm run build`, and `git diff --check`. If a concrete browser issue requires a fix, add the smallest source/test change, rerun all checks, and commit it separately.
