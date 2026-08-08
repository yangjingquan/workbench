# Workbench redesign design system

## Product context

Workbench is a personal operating system for one developer: projects, work records, plans, reminders, Todo execution, links, tools, accounting, and memos. The requested redesign targets four connected surfaces: persistent left navigation, overview dashboard, work records, and Todo board. The screens should feel like one coherent productivity workspace, not four unrelated templates.

## Current UI baseline to preserve

- Vue 3 + Element Plus app shell; desktop-first with mobile drawer/card fallbacks.
- Chinese UI copy; retain the existing labels and content model.
- The left rail contains Workspace items (总览看板, 项目管理, 工作记录, 工作计划, 事件提醒, Todo 看板, 快捷导航) and Tools items (开发工具箱 with badge 4, 记账存钱, 备忘录), followed by 系统设置 and 收起侧栏.
- Overview contains greeting/actions, four stat cards, focus tasks, work trend chart, Todo completion chart, recent records, and tool-usage chart.
- Records contains date range and keyword filters, list/calendar switch, a work-record table/list, and create/edit flow.
- Todo contains search/archive filters and a three-column board: 待处理, 进行中, 已完成. Cards support priority, tags, due date, timer, subtasks, drag/drop, archive, and batch completion.

## Existing visual tokens

- Typeface: Inter with Chinese system fallback.
- Light background `#f5f7fb`, white surfaces, `#f8f9fc` secondary surfaces, `#1b2434` text, `#8993a5` muted, `#e9edf5` lines.
- Brand family: indigo `#5b5ce2` / strong `#4546c6` / soft `#eef0ff`; accent `#8a7dff`; dark sidebar `#171a2b`; semantic green `#2bb673`, orange `#f09b45`, red `#e45f68`.
- Alternate ocean theme exists (`#159fd0` + `#18b89a`) and dark mode exists; keep them compatible.
- Cards use 13–14px radius, light borders, restrained shadows; controls/nav use 8–11px radius.

## Redesign guardrails

Keep all existing information architecture, Chinese labels, interaction affordances, and semantic statuses. Improve hierarchy, scanability, density, and the relationship between overview → records → Todos. Do not introduce unrelated marketing-landing-page patterns, decorative hero imagery, new fonts, neon gradients, or colors outside the token family. Use realistic placeholder data based on the current page copy. Make the four requested surfaces visibly comparable in each style direction.

## Three requested directions

1. **Quiet editorial / paper-like productivity** — airy grid, stronger typography hierarchy, subtle warm-neutral surface treatment while staying inside the existing indigo semantic family, calm navigation rail, generous whitespace.
2. **Focused command center** — denser power-user layout, crisp information bands, stronger active states, compact metric and board cards, fast scanning for active work and due dates.
3. **Soft spatial workspace** — layered panels, gentle color zoning, clear focus-task emphasis, more expressive but still restrained visual grouping between overview, records, and Todo execution.

Every generated direction must reuse the actual brand text and the current module content. Keep desktop viewport and show a coherent four-surface system board or linked screen set so the user can choose one direction.
