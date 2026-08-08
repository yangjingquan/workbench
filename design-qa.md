# Todo 看板设计 QA

## Source visual truth

- PC 端：[03-todo.html](/Users/yangjingquan/Downloads/PC端/03-todo.html)
- 移动端：[03-todo.html](/Users/yangjingquan/Downloads/移动端/03-todo.html)
- 参考截图：`/private/tmp/todo-reference-pc.png`（1440×900）、`/private/tmp/todo-reference-mobile.png`（390×844）

## Implementation evidence

- PC 截图：`/private/tmp/todo-app-pc-2.png`（1440×900，CSS viewport 1440×900，deviceScaleFactor 1）
- 移动端截图：`/private/tmp/todo-app-mobile-true.png`（390×844，CSS viewport 390×844，deviceScaleFactor 1）
- 本次计时及视觉微调检查：当前 Chrome 登录态 Todo 页面，桌面视口
- 路由：`/todos`
- 状态：浅色主题、已登录、包含待处理/进行中/已完成任务、包含子任务

## Comparison

### Full-view evidence

PC 端三列看板、列间距、进行中高亮列、完成列弱化、卡片圆角/阴影和整体灰白紫色调与参考稿一致。移动端以 Todo看板标题、归档入口、状态 Tab、双操作按钮和纵向三列任务卡组成，390px CSS 视口内无横向溢出。

### Focused regions

重点检查了 PC 看板列头/卡片状态标签、移动端顶部工具区/状态 Tab/任务卡/底部导航，以及任务卡右上角计时按钮、截止日期上方的实时用时和新建任务弹窗表单。没有需要单独裁剪的图片资产或复杂插画区域；图标均使用现有 Element Plus 图标组件。

## Required fidelity surfaces

- Fonts and typography: 保留现有应用的 Inter / 系统中文字体回退体系，字号、字重、行高与参考层级一致；参考稿使用的 Plus Jakarta Sans 未作为运行时网络依赖引入。
- Spacing and layout: PC 端 3 列空间布局和移动端单列布局已对齐；曾发现移动截图命令的物理窗口宽度与 CSS viewport 不一致，使用 CDP 强制 390×844 CSS viewport 复核后确认布局尺寸正确。
- Colors and tokens: 使用现有 `--primary`、`--accent`、`--surface`、`--line`、`--muted`、`--green`、`--red` 令牌，进行中/完成/高优先级状态颜色与参考稿一致。
- Image quality and asset fidelity: 设计稿没有业务图片资产；未新增占位图片、CSS 插画或自制 SVG，界面图标使用 Element Plus 图标组件。
- Copy and content: 页面固定文案更新为“Todo看板 / 高效管理，清晰规划”，交互文案和动态任务内容保持现有业务语义。
- Timer interaction: 计时按钮从卡片底部移至右上角，空闲态显示“计时”，运行态显示“暂停”；用时按 `HH:MM:SS` 每秒刷新，并放置在截止日期上方。
- Timer/card polish: 用时字号调整为 13px，截止日期调整为 12px；进行中列头移除右侧播放图标。
- New task form: 弹窗内所有 label 均与对应输入框、下拉框或文本域垂直居中对齐。
- Label rendering fix: 同时修正 label 自身的 `align-items`，避免盒子居中但文字仍贴近顶部。
- Mobile navigation: 移除所有页面底部快捷导航，保留顶部移动端菜单入口。
- Mobile Todo polish: 标题改为“Todo看板”，三个状态按钮用于快速定位到纵向展示的三列，顶部三个点仅作为拖拽手柄并保持水平居中；新建任务弹窗按钮居中，保存按钮宽度严格为取消按钮的 2 倍。
- Mobile toolbar width: 搜索框和操作行均填满移动端内容区；批量完成占 1/3，新建任务按钮占 2/3 并贴齐操作行右侧。

## Findings

- [P3] PC 顶部保留应用级工作区、项目、主题和强调色控制。设计稿顶部展示搜索框与新建按钮，而实现将 Todo 搜索和新建操作放在内容区工具栏。该差异是为了保留现有应用的全局上下文与主题能力，且核心操作仍位于首屏，不构成阻塞问题。
- [P3] 字体未引入远程 Plus Jakarta Sans，沿用项目已有字体栈，避免新增网络依赖；视觉层级通过字号、字重和字距补偿。

## Comparison history

1. 初次实现：PC/移动端完成 Soft Spatial Kanban 视觉层。
2. QA 发现：移动端截图在物理窗口宽度与 CSS viewport 不一致时出现裁切假象；补充 Todo 专属移动端宽度收敛与主内容 flex 约束。
3. 复核结果：在真实 390×844 CSS viewport 下，顶部操作、归档按钮、状态 Tab、卡片和底部导航均完整显示；PC 端复核无回归。

## Verification

- `npm run build`：通过。
- `npm test`：23/23 通过。
- `git diff --check`：通过。
- 已验证核心 UI 状态：PC 三列、移动端纵向三列、状态 Tab、空列状态、子任务展示、完成列弱化、进行中高亮。
- 已验证计时 UI：移动端任务卡右上角显示“开始计时”，用时位于截止日期上方；运行态使用现有后端 `start/pause` API，暂停不会提前生成工作记录。
- 已验证本次微调：进行中列头 `.column-state` 不再渲染，用时/截止日期字号生效，新建任务弹窗全部 label 与控件中心线偏差为 0px。
- 已验证移动端调整：底部导航节点为 0，三个状态列同时展示，状态按钮可滚动定位，顶部三个点保持拖拽手柄语义且水平居中，弹窗按钮中心对齐且宽度比例为 1:2。
- 已验证移动端工具栏：搜索框与操作行均使用内容区全宽，新建任务按钮占操作行 2/3 并抵达右侧边界。

## Implementation Checklist

- [x] PC 端三列 Todo 看板布局与状态色
- [x] 移动端任务流单列布局与状态切换
- [x] 归档、搜索、批量完成、新建、拖拽/移动状态入口保留
- [x] 子任务、计时、更多操作入口保留
- [x] 计时入口移动至卡片右上角，支持开始/暂停；当前任务用时显示在截止日期上方
- [x] 390px CSS viewport 响应式复核
- [x] 构建、测试、差异检查

## Follow-up Polish

- 如需 1:1 复刻设计稿，可在项目资源中引入 Plus Jakarta Sans 的本地字体文件，并将 PC 顶部操作区进一步改成设计稿的搜索框/新建按钮组合。

final result: passed

---

# 记账存钱页面设计 QA

## Source visual truth

- 桌面端参考截图：`/var/folders/gd/133fk3b92tl_glzpvs2kxf9r0000gn/T/codex-clipboard-5747b48d-f892-4b7d-a155-4144ec99fcc4.png`
- 移动端参考截图：`/var/folders/gd/133fk3b92tl_glzpvs2kxf9r0000gn/T/codex-clipboard-610dc729-3230-44ec-8c5c-725df7c6d2fd.png`、`/var/folders/gd/133fk3b92tl_glzpvs2kxf9r0000gn/T/codex-clipboard-cc839c18-f678-4346-83da-d4420c64def3.png`

## Implementation evidence

- 桌面端浏览器截图：`/private/tmp/accounting-app-pc.png`（1440×900，CSS viewport 1440×900，deviceScaleFactor 1）
- 移动端浏览器截图：`/private/tmp/accounting-app-mobile.png`（390×844，CSS viewport 390×844，deviceScaleFactor 1）
- 路由：`/accounting`
- 状态：浅色主题、已登录、月度统计、包含分类统计和账目明细

## Comparison

### Full-view evidence

桌面端表单与收支统计双栏结构、分类统计/明细纵向分区、浅灰背景和紫蓝主色与参考布局一致。移动端在 390px CSS viewport 下将表单、统计、分类和明细依次堆叠，三张收支卡保持同排，分类和明细改为可读卡片，未出现横向溢出。

### Focused region evidence

重点核对了账目类型切换、金额输入右侧加减按钮、日/月/年切换、明细操作区图标按钮和分页当前页。金额加减控件上下按钮已无中间间隙；分页页码使用明确的表面底色和主色选中态；移动端编辑/删除图标保留了足够的触控尺寸。

## Required fidelity surfaces

- Fonts and typography: 沿用项目既有 Inter / 系统中文字体回退栈；标题、面板标题、辅助文案与金额字号层级保持现有工作台语言，移动端金额和分页文字在 390px 下可读。
- Spacing and layout: 记账页面板和控件圆角收敛为更紧凑的 8–16px 区间；移动端统计卡使用三列等宽布局，分页页大小选择器调整为 100px 以避免“20/page”截断。
- Colors and visual tokens: 使用 `--primary`、`--surface-2`、`--line`、`--green`、`--red` 等既有令牌，收支语义色、选中态和分页当前页具有清晰对比。
- Image quality and asset fidelity: 参考图没有需要新增的业务图片；编辑和删除使用现有 Element Plus `EditPen` / `Delete` 图标组件，没有新增 CSS 插画、占位图或自制 SVG。
- Copy and content: 保持既有中文业务文案、动态金额、分类、日期和分页行为不变，仅将编辑/删除操作从文字改为带 aria-label/title 的图标按钮。

## Findings

- 无 P0/P1/P2 可执行问题。
- [P3] 参考截图中的桌面端浏览器宽度大于本次 1440px CSS 验证视口，当前报告按 CSS viewport 归一化对比；页面在更宽视口下保留现有自适应扩展能力。
- [P3] 参考截图中的移动端顶部内容处于不同滚动位置，本次分别核对了首屏表单、统计/分类区和明细/分页区，业务信息均完整保留。

## Interaction verification

- 日/月/年切换按钮可点击并触发统计范围更新。
- 支出/进账切换可点击并同步分类选项。
- 桌面端和移动端编辑/删除入口均为可访问图标按钮。
- 390px 下明细分页的页大小、上一页、当前页、下一页和跳转控件均保持在卡片内。
- 浏览器控制台错误数：0。

## Verification

- `npm run build`：通过。
- `npm test`：23/23 通过。
- 视觉复核：1440×900 桌面端、390×844 移动端均已完成。

## Comparison history

1. 初次调整：为记账页增加紧凑的切换控件、金额无缝加减按钮、图标操作按钮、清晰分页底色和移动端三列统计卡。
2. QA 发现：移动端分页页大小文本在 390px 下显示为 `20/p...`。
3. 修复并复核：将页大小选择器从 86px 放宽至 100px，最终显示完整 `20/page`，其它分页控件仍保持在卡片内。

## Implementation Checklist

- [x] 支出/进账切换减少圆角并统一选中态
- [x] 金额调节按钮无缝衔接并统一圆角
- [x] 日/月/年切换减少圆角并优化选中态
- [x] 编辑/删除改为 Element Plus 图标按钮
- [x] 分页页码增加清晰底色和当前页状态
- [x] 移动端表单、统计卡、分类卡、明细卡与分页布局优化
- [x] 构建、测试、桌面端与移动端视觉复核

final result: passed
