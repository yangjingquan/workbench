# Theme context

## Compact token summary

- Font: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif`; base 14px.
- Light canvas: `--bg #f5f7fb`; surfaces `#fff` / `#f8f9fc`; text `#1b2434`; muted `#8993a5`; line `#e9edf5`.
- Indigo brand: primary `#5b5ce2`, strong `#4546c6`, soft `#eef0ff`, accent `#8a7dff`; sidebar `#171a2b`; active `#5b5de4`.
- Semantic colors: green `#2bb673`, orange `#f09b45`, red `#e45f68`; soft fills `#e8fbf1`, `#fff3e6`, `#ffedef`.
- Dark canvas: `--bg #10121c` / `#0f1724` depending on later theme block; surface `#181b29`; text `#edf0fa`; line `#2b3043`.
- Ocean alternative: primary `#159fd0`, strong `#0e7ea8`, accent `#18b89a`, sidebar `#0e3a4a`.
- Layout: 238px sidebar, collapsed 76px; 76px desktop topbar; content padding 30px 38px 45px; 14px cards; 16–18px grid gaps.
- Radius: 8–11px controls/nav, 13–14px cards/panels, 20px login card; shadow `0 12px 30px rgba(37,45,91,.06)`.
- Responsive breakpoint: 760px (mobile drawer, stacked grids, card lists); 1100px (reduced content padding and two-column stats).

## Raw source excerpts

The canonical full source is `frontend/src/styles.css` (556 lines) and must be passed directly as context for design generation. The most relevant selectors are reproduced below.

```css
:root { --bg: #f5f7fb; --surface: #fff; --surface-2: #f8f9fc; --line: #e9edf5; --text: #1b2434; --muted: #8993a5; --primary: #5b5ce2; --primary-soft: #eef0ff; --green: #2bb673; --orange: #f09b45; --red: #e45f68; --sidebar: #171a2b; --shadow: 0 12px 30px rgba(37, 45, 91, .06); }
html.dark { --bg: #10121c; --surface: #181b29; --surface-2: #202435; --line: #2b3043; --text: #edf0fa; --muted: #8e97ae; --primary-soft: #272a52; --sidebar: #0b0d15; }
body { margin: 0; background: var(--bg); color: var(--text); font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif; font-size: 14px }
.sidebar { flex: 0 0 238px; background: var(--sidebar); color: #9da5be; padding: 22px 12px 16px }
.topbar { height: 76px; padding: 0 38px; background: var(--surface); border-bottom: 1px solid var(--line) }
.content-scroll { padding: 30px 38px 45px }
.stat-card, .panel, .form-card, .link-card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--shadow) }
.todo-column { background: var(--surface-2); border: 1px solid var(--line); border-radius: 13px; padding: 13px; min-height: 420px }
.todo-card { background: var(--surface); border: 1px solid var(--line); padding: 15px; border-radius: 11px; box-shadow: 0 4px 10px #3d42660b }
```
