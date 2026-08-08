# Page dependency trees

## `/dashboard` — Overview

- `frontend/src/pages/Dashboard.vue`
  - `frontend/src/components/StatCard.vue`
  - `frontend/src/stores/index.js`
  - `frontend/src/api/http.js`
  - `frontend/src/layouts/AppLayout.vue`
    - `frontend/src/components/ReminderPoll.vue`
    - `frontend/src/layouts/mobileNav.js`
    - `frontend/src/router/index.js`
  - `frontend/src/styles.css`

## `/records` — Work records

- `frontend/src/pages/Records.vue`
  - `frontend/src/stores/index.js`
  - `frontend/src/api/http.js`
  - Element Plus table, date picker, input, radio group, form, dialog, tag, button, empty
  - `frontend/src/layouts/AppLayout.vue`
  - `frontend/src/styles.css`

## `/todos` — Todo board

- `frontend/src/pages/Todos.vue`
  - `frontend/src/stores/index.js`
  - `frontend/src/api/http.js`
  - Element Plus input, checkbox, tooltip, select, dropdown, dialog, form, button, empty
  - `frontend/src/layouts/AppLayout.vue`
  - `frontend/src/styles.css`

## Other route entries

- `/projects` → `frontend/src/pages/Projects.vue` → stores, api, AppLayout, styles
- `/projects/:id` → `frontend/src/pages/ProjectDetail.vue` → stores, api, AppLayout, styles
- `/plans` → `frontend/src/pages/Plans.vue` → stores, api, AppLayout, styles
- `/reminders` → `frontend/src/pages/Reminders.vue` → api, reminderTime, AppLayout, styles
- `/links` → `frontend/src/pages/Links.vue` → api, AppLayout, styles
- `/toolkit` → `frontend/src/pages/Toolkit.vue` → api, AppLayout, styles
- `/accounting` → `frontend/src/pages/Accounting.vue` → api, stores, AppLayout, styles
- `/memos` → `frontend/src/pages/Memos.vue` → api, stores, AppLayout, styles
- `/profile` → `frontend/src/pages/Profile.vue` → api, stores, AppLayout, styles
- `/settings` → `frontend/src/pages/Settings.vue` → api, stores, theme, AppLayout, styles
