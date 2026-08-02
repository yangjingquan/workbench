# 移动端响应式适配 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Dev Workbench 在 390px 等手机宽度下拥有真正可用的导航、内容布局和表单操作体验，同时保持桌面端现有视觉语言与业务行为。

**Architecture:** 在现有 `AppLayout.vue` 中增加只在移动端显示的抽屉导航，复用当前路由数组和主题/账号操作；桌面侧栏保持原有结构和持久化折叠状态。将移动端样式集中补充到 `styles.css` 的 `760px` 断点中，按页面类型处理标题、工具条、面板、表格、表单、弹窗和设置项的换行与滚动。

**Tech Stack:** Vue 3 Composition API、Vue Router 4、Element Plus、Vite、Node.js built-in `node:test`。

## Global Constraints

- 手机端隐藏侧栏，顶部增加菜单入口，导航使用现有 `mainNav` 和工具导航，不新增路由。
- 390px 宽度下主布局不出现页面级横向滚动；内容只允许在表格容器内部横向滚动。
- 保持现有视觉语言、主题变量、路由和业务 API，不新增运行时依赖。
- 触控目标保持至少约 40px 高度；菜单按钮提供中文 `aria-label`，移动导航有可见关闭按钮。
- 760px 以上桌面布局的侧栏、顶部栏和主要网格结构保持不变。
- 验证必须运行前端测试和 `npm run build`；后端不可用时不得伪造登录后数据截图。

---

## 文件结构与职责

- Create: `frontend/src/layouts/mobileNav.js` — 提供移动导航的纯状态转换函数，供布局组件使用并可用 Node 测试。
- Create: `frontend/src/layouts/mobileNav.test.js` — 测试移动导航初始、打开、切换和关闭行为。
- Create: `frontend/src/layouts/mobileLayoutContract.test.js` — 不启动浏览器的布局契约测试，检查布局模板中必须存在的稳定钩子。
- Create: `frontend/src/layouts/mobileStyleContract.test.js` — 不启动浏览器的样式契约测试，检查移动断点中必须存在的响应式规则。
- Modify: `frontend/src/layouts/AppLayout.vue` — 添加移动菜单按钮、抽屉、遮罩、关闭/路由切换行为和必要图标。
- Modify: `frontend/src/styles.css` — 添加移动导航、表格滚动、页面标题/工具条/表单/弹窗/页面专属布局的响应式样式。
- Modify: `frontend/package.json` — 增加使用 Node built-in test runner 的 `test` 脚本。

## Task 1: 建立移动导航状态契约

**Files:**
- Create: `frontend/src/layouts/mobileNav.test.js`
- Create: `frontend/src/layouts/mobileNav.js`
- Modify: `frontend/package.json`

**Interfaces:**
- Produces `createMobileNavState(open = false): { open: boolean }`。
- Produces `toggleMobileNav(state): { open: boolean }`，返回新状态且不修改传入对象。
- Produces `closeMobileNav(): { open: false }`，返回一个关闭状态。

- [ ] **Step 1: 先写失败测试**

```js
import assert from 'node:assert/strict'
import test from 'node:test'
import { closeMobileNav, createMobileNavState, toggleMobileNav } from './mobileNav.js'

test('mobile navigation starts closed and toggles without mutating the source state', () => {
  const closed = createMobileNavState()
  const opened = toggleMobileNav(closed)

  assert.deepEqual(closed, { open: false })
  assert.deepEqual(opened, { open: true })
  assert.deepEqual(toggleMobileNav(opened), { open: false })
})

test('mobile navigation can always be closed', () => {
  assert.deepEqual(closeMobileNav(), { open: false })
})
```

- [ ] **Step 2: 运行测试确认它按预期失败**

Run: `cd frontend && node --test src/layouts/mobileNav.test.js`

Expected: FAIL because `src/layouts/mobileNav.js` does not exist yet。

- [ ] **Step 3: 写最小实现**

```js
export function createMobileNavState(open = false) {
  return { open: Boolean(open) }
}

export function toggleMobileNav(state) {
  return { open: !state.open }
}

export function closeMobileNav() {
  return { open: false }
}
```

在 `frontend/package.json` 的 `scripts` 中增加：

```json
"test": "node --test src/utils/*.test.js src/layouts/*.test.js"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && node --test src/layouts/mobileNav.test.js`

Expected: 2 tests pass with 0 failures。

- [ ] **Step 5: 提交状态契约**

```bash
git add frontend/package.json frontend/src/layouts/mobileNav.js frontend/src/layouts/mobileNav.test.js
git commit -m "test: add mobile navigation state contract"
```

## Task 2: 接入移动端抽屉导航

**Files:**
- Create: `frontend/src/layouts/mobileLayoutContract.test.js`
- Modify: `frontend/src/layouts/AppLayout.vue`

**Interfaces:**
- Consumes the three state functions from `mobileNav.js`。
- Produces a `.mobile-menu-button` trigger、`.mobile-nav-layer` overlay、`.mobile-nav-panel` drawer and `.mobile-nav-close` close button。
- Produces `toggleMobileMenu()`、`closeMobileMenu()` functions in the component scope。

- [ ] **Step 1: 先写失败的布局契约测试**

```js
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(new URL('./AppLayout.vue', import.meta.url), 'utf8')

test('AppLayout exposes a mobile menu trigger and dismissible drawer', () => {
  assert.match(source, /class="mobile-menu-button"/)
  assert.match(source, /aria-label="打开移动端导航"/)
  assert.match(source, /class="mobile-nav-layer"/)
  assert.match(source, /class="mobile-nav-panel"/)
  assert.match(source, /class="mobile-nav-close"/)
  assert.match(source, /@click="closeMobileMenu"/)
  assert.match(source, /watch\(\(\) => route\.fullPath, closeMobileMenu\)/)
})
```

- [ ] **Step 2: 运行测试确认它失败**

Run: `cd frontend && node --test src/layouts/mobileLayoutContract.test.js`

Expected: FAIL because the current layout has no mobile menu trigger or drawer hooks。

- [ ] **Step 3: 在 AppLayout 中实现最小移动导航行为**

在 `<script setup>` 中：

```js
import { reactive, ref, watch } from 'vue'
import { Menu, Close } from '@element-plus/icons-vue'
import { closeMobileNav, createMobileNavState, toggleMobileNav } from './mobileNav'

const mobileNav = reactive(createMobileNavState())
function toggleMobileMenu() { Object.assign(mobileNav, toggleMobileNav(mobileNav)) }
function closeMobileMenu() { Object.assign(mobileNav, closeMobileNav(mobileNav)) }
watch(() => route.fullPath, closeMobileMenu)
```

在 `.topbar` 内、`.breadcrumb` 前添加：

```vue
<button class="mobile-menu-button" type="button" aria-label="打开移动端导航" @click="toggleMobileMenu">
  <el-icon><Menu /></el-icon>
</button>
```

在 `.app-shell` 内、`<main>` 后添加：

```vue
<Transition name="mobile-nav">
  <div v-if="mobileNav.open" class="mobile-nav-layer" @keydown.esc="closeMobileMenu">
    <button class="mobile-nav-backdrop" type="button" aria-label="关闭移动端导航" @click="closeMobileMenu" />
    <aside class="mobile-nav-panel" aria-label="移动端导航">
      <div class="mobile-nav-header">
        <div class="brand"><div class="brand-mark">⌘</div><div class="brand-copy"><b>Workbench</b><span>小胖的工作台</span></div></div>
        <button class="mobile-nav-close" type="button" aria-label="关闭移动端导航" @click="closeMobileMenu"><el-icon><Close /></el-icon></button>
      </div>
      <nav class="mobile-nav-list">
        <div class="nav-section">WORKSPACE</div>
        <RouterLink v-for="item in mainNav" :key="item.path" :to="item.path" class="nav-item" @click="closeMobileMenu"><el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span></RouterLink>
        <div class="nav-section">TOOLS</div>
        <RouterLink to="/toolkit" class="nav-item" @click="closeMobileMenu"><el-icon><Tools /></el-icon><span>开发工具箱</span><span class="nav-badge">4</span></RouterLink>
        <RouterLink to="/accounting" class="nav-item" @click="closeMobileMenu"><el-icon><Wallet /></el-icon><span>记账存钱</span></RouterLink>
        <RouterLink to="/memos" class="nav-item" @click="closeMobileMenu"><el-icon><Memo /></el-icon><span>备忘录</span></RouterLink>
        <RouterLink to="/settings" class="nav-item" @click="closeMobileMenu"><el-icon><Setting /></el-icon><span>系统设置</span></RouterLink>
      </nav>
    </aside>
  </div>
</Transition>
```

保持原有桌面 `.sidebar`、`app.collapsed`、用户下拉菜单和搜索弹窗不变；移动抽屉只复用路由和视觉类，不复制任何业务逻辑。

- [ ] **Step 4: 运行布局契约和完整单元测试**

Run: `cd frontend && node --test src/layouts/mobileLayoutContract.test.js src/layouts/mobileNav.test.js src/utils/*.test.js`

Expected: all tests pass with 0 failures。

- [ ] **Step 5: 提交移动导航**

```bash
git add frontend/src/layouts/AppLayout.vue frontend/src/layouts/mobileLayoutContract.test.js
git commit -m "feat: add mobile drawer navigation"
```

## Task 3: 补齐移动端响应式样式

**Files:**
- Create: `frontend/src/layouts/mobileStyleContract.test.js`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes the stable class hooks from `AppLayout.vue` and existing page classes。
- Produces responsive rules under `@media (max-width: 760px)` without changing desktop rules above the breakpoint。

- [ ] **Step 1: 先写失败的样式契约测试**

```js
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const styles = readFileSync(new URL('../styles.css', import.meta.url), 'utf8')

test('mobile styles provide navigation, table, dialog, and stacked layout rules', () => {
  assert.match(styles, /\.mobile-menu-button\s*\{[^}]*display:\s*none/)
  assert.match(styles, /\.mobile-nav-layer\s*\{[^}]*display:\s*none/)
  assert.match(styles, /@media \(max-width:\s*760px\)/)
  assert.match(styles, /\.sidebar\s*\{\s*display:\s*none/)
  assert.match(styles, /\.mobile-menu-button\s*\{[^}]*display:\s*grid/)
  assert.match(styles, /\.table-card\s*\{[^}]*overflow-x:\s*auto/)
  assert.match(styles, /\.page-heading\s*\{[^}]*flex-direction:\s*column/)
  assert.match(styles, /\.setting-row\s*\{[^}]*flex-direction:\s*column/)
  assert.match(styles, /\.el-dialog\s*\{[^}]*width:\s*calc\(100vw - 32px\)/)
})
```

- [ ] **Step 2: 运行测试确认它失败**

Run: `cd frontend && node --test src/layouts/mobileStyleContract.test.js`

Expected: FAIL because the current styles do not contain the mobile drawer and explicit table/dialog rules。

- [ ] **Step 3: 实现移动端样式**

在现有通用样式中增加默认隐藏的移动导航钩子：

```css
.mobile-menu-button,
.mobile-nav-layer { display: none; }
```

在现有移动断点中实现以下行为：

```css
@media (max-width: 760px) {
  .sidebar { display: none; }
  .mobile-menu-button { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 10px; color: var(--muted); background: transparent; flex: 0 0 40px; }
  .mobile-menu-button:hover, .mobile-menu-button:focus-visible { background: var(--primary-soft); color: var(--primary); }
  .mobile-nav-layer { display: block; position: fixed; inset: 0; z-index: 2000; }
  .mobile-nav-backdrop { position: absolute; inset: 0; width: 100%; height: 100%; background: rgba(8, 12, 28, .42); }
  .mobile-nav-panel { position: relative; z-index: 1; width: min(300px, calc(100vw - 56px)); height: 100%; padding: 22px 12px 16px; overflow-y: auto; background: var(--sidebar); color: var(--sidebar-muted); box-shadow: 18px 0 40px rgba(8, 12, 28, .2); }
  .mobile-nav-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; padding: 0 10px 22px; }
  .mobile-nav-close { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 10px; color: var(--sidebar-muted); background: transparent; }
  .mobile-nav-close:hover, .mobile-nav-close:focus-visible { color: #fff; background: var(--sidebar-hover); }
  .mobile-nav-list .nav-item { height: 44px; }
  .mobile-nav-enter-active, .mobile-nav-leave-active { transition: opacity .2s ease; }
  .mobile-nav-enter-active .mobile-nav-panel, .mobile-nav-leave-active .mobile-nav-panel { transition: transform .2s ease; }
  .mobile-nav-enter-from, .mobile-nav-leave-to { opacity: 0; }
  .mobile-nav-enter-from .mobile-nav-panel, .mobile-nav-leave-to .mobile-nav-panel { transform: translateX(-100%); }

  .topbar { height: 64px; flex-basis: 64px; padding: 0 14px; gap: 8px; }
  .breadcrumb { min-width: 0; gap: 8px; font-size: 13px; }
  .breadcrumb > span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .top-actions { gap: 2px; }
  .icon-button { width: 34px; height: 34px; }
  .avatar-wrap { margin-left: 2px; }
  .content-scroll { padding: 20px 16px 32px; }
  .page-heading { align-items: flex-start; flex-direction: column; gap: 14px; margin-bottom: 20px; }
  .page-heading h1 { font-size: 22px; }
  .page-actions, .toolbar, .toolbar-left, .toolbar-right { width: 100%; flex-wrap: wrap; }
  .page-actions { align-items: stretch; }
  .page-actions .el-button { flex: 1 1 auto; min-height: 40px; }
  .toolbar { align-items: stretch; flex-direction: column; }
  .toolbar-left, .toolbar-right { justify-content: flex-start; }
  .toolbar-left > .el-input, .toolbar-left > .el-date-editor { width: 100% !important; flex: 1 1 100%; }
  .toolbar-right .el-button { min-height: 40px; }
  .panel, .form-card { padding: 16px; }
  .panel-header { align-items: flex-start; gap: 10px; }
  .stats-grid { gap: 10px; }
  .stat-card { padding: 16px 14px; }
  .stat-value { font-size: 24px; }
  .chart { height: 220px; }
  .table-card { overflow-x: auto; }
  .table-card > .el-table { min-width: 720px; }
  .account-category-panel, .account-records-panel { overflow-x: auto; }
  .account-category-panel > .el-table, .account-records-panel > .el-table { min-width: 620px; }
  .todo-footer { flex-wrap: wrap; gap: 8px; }
  .todo-footer .timer-link { margin-left: auto; margin-right: 0; }
  .setting-row { align-items: stretch; flex-direction: column; gap: 12px; padding: 16px; }
  .setting-row .el-select, .setting-row .el-segmented, .setting-row .two-col { width: 100% !important; }
  .danger-zone { align-items: stretch; flex-direction: column; gap: 14px; }
  .account-period-picker { width: 100%; }
  .account-stat-cards { grid-template-columns: 1fr; }
  .category-create-row { align-items: stretch; }
  .category-create-row > .el-select, .category-create-row > .el-input, .category-create-row > .el-button { width: 100% !important; }
  .memo-detail .panel-header { flex-wrap: wrap; }
  .el-dialog { width: calc(100vw - 32px) !important; margin: 0 auto; }
  .el-dialog__body { padding: 0 16px 16px; }
  .el-dialog__footer { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
}
```

保留原有 `grid-2`、`todo-board`、`tool-grid` 单列规则和 `link-grid` 两列规则；只将通用的标题、工具条、表格、设置项和弹窗规则合并到同一个 `760px` 断点，避免继续追加相互覆盖的零散媒体查询。

- [ ] **Step 4: 运行样式契约和完整单元测试**

Run: `cd frontend && npm test`

Expected: all existing utility tests plus the four mobile layout tests pass with 0 failures。

- [ ] **Step 5: 提交响应式样式**

```bash
git add frontend/src/styles.css frontend/src/layouts/mobileStyleContract.test.js
git commit -m "feat: refine mobile responsive layouts"
```

## Task 4: 构建与移动宽度验证

**Files:**
- No new source files.
- Verify: `frontend/dist/` generated output only; do not commit generated output unless the repository already tracks it.

**Interfaces:**
- Consumes the completed mobile drawer and responsive CSS。
- Produces fresh test, build, and viewport evidence for 390px and 768px widths。

- [ ] **Step 1: 运行完整测试**

Run: `cd frontend && npm test`

Expected: Node test runner exits 0 and reports 0 failures。

- [ ] **Step 2: 运行生产构建**

Run: `cd frontend && npm run build`

Expected: Vite exits 0；已有 `%VITE_BUILD_ID%` 和大 chunk 警告可以保留，但不能出现编译错误。

- [ ] **Step 3: 检查差异和桌面布局未被意外改写**

Run: `git diff --check && git diff -- frontend/src/layouts/AppLayout.vue frontend/src/styles.css`

Expected: no whitespace errors；差异仅涉及移动抽屉、移动断点和测试/脚本文件。

- [ ] **Step 4: 在本地预览检查 390px 和 768px**

使用现有本地开发服务器，在浏览器 viewport 设为 `{ width: 390, height: 844 }` 与 `{ width: 768, height: 900 }`，检查：

1. 登录页不出现横向溢出。
2. 登录后若后端可用，顶部菜单可打开/关闭，点击路由后抽屉自动关闭。
3. 看板标题、统计卡、图表、表格页工具条、Todo 单列、工具箱单列、记账/备忘录/设置表单不被裁切。
4. 用页面只读测量确认 `document.documentElement.scrollWidth <= document.documentElement.clientWidth`；表格横向滚动仅发生在表格容器内部。

若后端仍不可用，只报告登录页和静态构建结果，并明确说明登录后页面无法做真实数据截图，不伪造验收结果。

- [ ] **Step 5: 提交验证结果**

```bash
git status --short
git log -3 --oneline
```

确认工作树只包含预期变更，并把实际测试、构建和可验证页面范围写入交付说明。
