# Workbench Theme System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, user-selectable blue-purple or sky-blue/teal accent theme that styles the login page and every authenticated page without changing business behavior.

**Architecture:** Keep one shared semantic token layer in `frontend/src/styles.css`. Extend the Pinia app store with an `accentTheme` state that applies `data-accent-theme` to `<html>` and persists it in local storage. Expose the same state through the authenticated top bar, system settings, and public login page; Dashboard charts will read the active CSS tokens and re-render on either theme or light/dark changes.

**Tech Stack:** Vue 3, Pinia, Element Plus, ECharts, Vite, CSS custom properties, localStorage.

## Global Constraints

- Preserve existing routes, API calls, authentication flow, data structures, and page-level information architecture.
- Default accent theme is `indigo`; alternate accent theme is `ocean`.
- Persist accent theme under `workbench_accent_theme`; preserve independent light/dark state under `workbench_theme`.
- Do not add runtime dependencies.
- Keep existing successful, warning, danger, income, and expense semantic colors distinct from the active accent theme.
- Verify desktop frontend build with `npm --prefix frontend run build:desktop`.

### Task 1: Add persistent accent-theme state

**Files:**
- Modify: `frontend/src/stores/index.js`
- Modify: `frontend/src/main.js` if root theme initialization needs to run before mount
- Test: `frontend/src/stores/index.js` behavior through the frontend build and manual localStorage checks

**Interfaces:**
- Produces `accentTheme`, `setAccentTheme(value)`, and `toggleAccentTheme()` from `useAppStore()`.
- `accentTheme` accepts only `indigo` or `ocean`; invalid or missing localStorage values fall back to `indigo`.
- `setAccentTheme()` updates `document.documentElement.dataset.accentTheme`, stores `workbench_accent_theme`, and does not change `theme`.

- [ ] **Step 1: Define the stored accent theme with a safe fallback**

  Add a small normalization helper near the top of the store and initialize the state from `localStorage.getItem('workbench_accent_theme')`, accepting only `indigo` and `ocean`.

- [ ] **Step 2: Implement DOM application and persistence**

  Add `applyAccentTheme(value)` and call it from `setAccentTheme()` and `initTheme()`. `initTheme()` must apply both the existing `dark` class and the accent `data-accent-theme` attribute.

- [ ] **Step 3: Add the toggle action and return the new state**

  Implement `toggleAccentTheme()` as `setAccentTheme(accentTheme.value === 'indigo' ? 'ocean' : 'indigo')`, then expose all new state and actions from the store return object.

- [ ] **Step 4: Build the frontend to validate the store changes**

  Run `npm --prefix frontend run build:desktop`.

  Expected: Vite exits with code 0 and emits `frontend/dist/index.html` without Vue or syntax errors.

### Task 2: Replace hard-coded colors with semantic theme tokens

**Files:**
- Modify: `frontend/src/styles.css`

**Interfaces:**
- `:root` remains the indigo default token set.
- `[data-accent-theme="ocean"]` overrides only accent-dependent variables.
- `html.dark` and `html.dark[data-accent-theme="ocean"]` provide readable dark variants.
- All shared UI states consume variables such as `--primary`, `--primary-strong`, `--primary-soft`, `--accent`, `--accent-soft`, `--sidebar`, and `--sidebar-active`.

- [ ] **Step 1: Add complete semantic token sets**

  Extend the current root variables with `--primary-strong`, `--accent`, `--accent-soft`, `--sidebar-active`, and theme-aware text / border / shadow tokens. Add ocean overrides for the sky-blue/teal palette and dark ocean overrides for dark mode.

- [ ] **Step 2: Update shared shell and control styles**

  Replace hard-coded purple values in `.brand-mark`, active navigation, `.el-button--primary`, `.soft-button`, focus rings, active memo borders, link card hover borders, login emphasis, and chart-adjacent utility styles with the semantic tokens. Add explicit hover/focus/disabled states for buttons, inputs, radios, selects, switches, and links where Element Plus defaults otherwise retain stale blue-purple values.

- [ ] **Step 3: Update page surfaces and semantic status styles**

  Keep `--green`, `--orange`, and `--red` independent of the accent theme. Convert static success and selected backgrounds that currently use literal hex values to `--green-soft`, `--orange-soft`, and `--red-soft`. Ensure tables, dialogs, calendars, Todo cards, memo selection, account panels, and settings rows use the shared surface, line, text, and accent tokens.

- [ ] **Step 4: Add responsive and focus polish without changing structure**

  Preserve existing breakpoints while ensuring the topbar theme action, login theme action, and settings selector remain usable below 760px. Add `:focus-visible` outlines using `--primary` for keyboard users.

- [ ] **Step 5: Build after the token migration**

  Run `npm --prefix frontend run build:desktop`.

  Expected: Vite exits with code 0 and all pages compile with the new CSS variables.

### Task 3: Add theme controls to the app shell and login page

**Files:**
- Modify: `frontend/src/layouts/AppLayout.vue`
- Modify: `frontend/src/pages/Login.vue`

**Interfaces:**
- App shell exposes a quick accent-theme toggle with an accessible title and `aria-label` that describes the next theme.
- Login page exposes the same toggle without requiring a session.
- Both controls call the shared Pinia store action and display the current theme name through a tooltip or visually hidden label.

- [ ] **Step 1: Add the authenticated quick switch**

  Keep the existing light/dark moon/sun control. Add a neighboring accent-theme button that calls `app.toggleAccentTheme()` and uses an icon plus a label/title such as `切换到天蓝青绿` or `切换到蓝紫品牌` based on `app.accentTheme`.

- [ ] **Step 2: Add a public login theme switch**

  Add a compact control to the login brand/header area. It must work before authentication, use the same store action, and not alter the login submit function or encryption flow.

- [ ] **Step 3: Verify navigation continuity**

  Confirm the router's existing `store.initTheme()` path applies both the light/dark class and accent data attribute when entering `/login` or an authenticated route.

### Task 4: Redesign the login page and authenticated shell using the shared tokens

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/pages/Login.vue` only if semantic class hooks are needed
- Modify: `frontend/src/layouts/AppLayout.vue` only if semantic class hooks are needed

**Interfaces:**
- No new data or API interfaces.
- Existing classes remain available to all page templates so current routes render unchanged.

- [ ] **Step 1: Rebalance the login composition**

  Use a brighter, more spacious login surface while keeping the current brand copy and form. The indigo theme retains a restrained purple-blue gradient; the ocean theme shifts the glow, grid, heading emphasis, inputs, and primary button to sky-blue/teal. Keep the form centered on desktop and single-column on mobile.

- [ ] **Step 2: Refresh the app shell**

  Use a deep indigo sidebar for the brand theme and deep ocean sidebar for the alternate theme. Keep the main content bright, with larger breathing room, low-contrast borders, lighter shadows, and clear page-heading hierarchy. Ensure the active nav, badges, avatar online dot, top actions, and breadcrumb remain legible in both accent themes.

- [ ] **Step 3: Refresh shared content patterns**

  Apply the visual language to panels, stat cards, tables, forms, dialogs, Todo columns, link cards, memo selection, account summaries, settings rows, and empty states through the semantic tokens instead of page-specific overrides.

### Task 5: Add settings selector and synchronize Dashboard charts

**Files:**
- Modify: `frontend/src/pages/Settings.vue`
- Modify: `frontend/src/pages/Dashboard.vue`

**Interfaces:**
- Settings adds an accent selector backed by `app.accentTheme`.
- Dashboard chart color resolution reads `--primary`, `--accent`, `--green`, `--muted`, and `--line` from the document root; its existing `watch()` re-renders when accent theme changes.

- [ ] **Step 1: Add the “主题色系” setting row**

  Add a row above the current theme-mode setting using `el-segmented` or `el-radio-group` with values `indigo` and `ocean`. Initialize it from `app.accentTheme`; when changed, call `app.setAccentTheme(value)` immediately so the preview updates before saving.

- [ ] **Step 2: Preserve settings save behavior**

  Keep the existing server config save payload for light/dark theme, sidebar, reminders, view, and work hours. The accent theme is local UI preference and must remain persisted by the store without being sent to the backend unless the existing config contract is explicitly extended.

- [ ] **Step 3: Update Dashboard chart palette**

  Extend `colors()` to read `--primary-strong` and `--accent` and use the active accent for the line, bar, pie pending segment, and area fill. Use `app.accentTheme` in the existing watcher so a theme switch disposes and redraws charts with the new palette.

- [ ] **Step 4: Build and inspect both settings states**

  Run `npm --prefix frontend run build:desktop`, then manually confirm changing the selector updates the page immediately and survives a refresh.

### Task 6: Verify the complete frontend and desktop packaging path

**Files:**
- No source changes expected unless verification exposes a concrete issue.

- [ ] **Step 1: Run the frontend production build**

  Run `npm --prefix frontend run build:desktop`.

  Expected: exit code 0 with no compile errors.

- [ ] **Step 2: Run the desktop renderer copy step**

  Run `npm --prefix desktop run build:renderer`.

  Expected: frontend output is copied into `desktop/renderer` and the command exits 0.

- [ ] **Step 3: Check source-level theme coverage**

  Run `rg -n "#5b5ce2|#5b5de4|#696aff|#aeb0ff|#b8baff|#8185eb|#8d90ff" frontend/src` and inspect any remaining matches. Remaining literal colors must be intentional non-theme semantic colors or removed.

- [ ] **Step 4: Check the desktop package if requested by the final handoff**

  Run `npm --prefix desktop run package:mac` only after the renderer build is green. On this arm64 macOS environment, use the approved hdiutil path if the sandbox blocks DMG creation.

- [ ] **Step 5: Report the verified outputs**

  Include the changed files, build commands and exit status, theme persistence behavior, and any packaging limitation such as unsigned macOS artifacts.

