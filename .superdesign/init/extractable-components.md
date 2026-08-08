# Extractable DraftComponents

## Layout

### AppShell
- Source: `frontend/src/layouts/AppLayout.vue`
- Category: layout
- Description: Persistent desktop shell with sidebar, topbar, route content, mobile drawer, global search, and reminder poller.
- Extractable props: `activeItem` (route-derived), `collapsed` (boolean), `workspaceName`, `projectName`, `showSearch`.
- Hardcoded: Workbench brand, Chinese nav labels, icon choices, CSS classes, route destinations.

### Sidebar
- Source: `frontend/src/layouts/AppLayout.vue`
- Category: layout
- Description: Dark workspace/tool navigation with active gradient item, tool badge, settings, and collapse control.
- Extractable props: `activeItem`, `collapsed`, `toolBadgeCount`.
- Hardcoded: Workbench mark, section labels, nav text, icon names, CSS.

### Topbar
- Source: `frontend/src/layouts/AppLayout.vue`
- Category: layout
- Description: Breadcrumb plus workspace/project filters, search, theme toggles, accent toggle, and user menu.
- Extractable props: `pageTitle`, `workspaceName`, `projectName`, `theme`, `accentTheme`, `avatarUrl`.
- Hardcoded: PERSONAL OS eyebrow, icon names, menu labels, CSS.

## Basic

### StatCard
- Source: `frontend/src/components/StatCard.vue`
- Category: basic
- Description: Metric card with label, icon, value, trend, and explanatory footnote.
- Extractable props: `label`, `value`, `foot`, `trend`, `icon`, `tone`.
- Hardcoded: markup and class structure.

### StatusTag
- Source: `frontend/src/components/StatusTag.vue`
- Category: basic
- Description: Compact status or priority pill.
- Extractable props: `label`, `text`, `tone`.
- Hardcoded: markup and class structure.

### BaseDialog
- Source: `frontend/src/components/BaseDialog.vue`
- Category: basic
- Description: Element Plus dialog wrapper with footer slot.
- Extractable props: `modelValue`.
- Hardcoded: Element Plus dialog composition.

### BaseSelect
- Source: `frontend/src/components/BaseSelect.vue`
- Category: basic
- Description: Element Plus select with normalized option input.
- Extractable props: `options`.
- Hardcoded: Element Plus option mapping.
