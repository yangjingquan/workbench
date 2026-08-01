# Dev Workbench · 程序员个人工作台

一套本地优先的个人工作台：用来记录工作、安排计划、管理 Todo、维护常用链接、接收提醒，并通过轻量统计帮助复盘自己的工作节奏。

## 技术栈

- 前端：Vue 3、Vite、Element Plus、Vue Router 4、Pinia、ECharts
- 后端：Python FastAPI、SQLAlchemy ORM、JWT、bcrypt
- 数据库：MySQL 8.0（默认连接 `root / changeme_root`）

## 目录

```text
backend/
  app/
    api/       REST 路由与鉴权依赖
    core/      配置与密码/JWT 安全逻辑
    db/        SQLAlchemy Engine、Session、Base
    models/    业务数据模型
  sql/init.sql 显式 MySQL 初始化脚本
  requirements.txt
frontend/
  src/api/    Axios 实例与接口封装
  src/stores/ Pinia 登录、主题、布局状态
  src/layouts/全局侧边栏+内容布局
  src/pages/  登录、看板及八大模块页面
desktop/
  main.cjs    Electron 主进程与默认浏览器跳转处理
  preload.cjs 安全隔离的桌面能力入口
  build.mjs   复制桌面生产版前端资源
```

## 环境准备

### 1. MySQL

确认 MySQL 8.0 已启动，并使用有建库权限的账号执行：

```bash
mysql -uroot -pchangeme_root < backend/sql/init.sql
```

默认数据库名是 `workbench`。如果账号或地址不同，复制 `backend/.env.example` 为 `backend/.env`，修改 `DATABASE_URL`：

```env
DATABASE_URL=mysql+pymysql://用户名:密码@127.0.0.1:3306/数据库名?charset=utf8mb4
JWT_SECRET_KEY=换成随机长字符串
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,null
```

### 2. 启动后端

Python 3.11+ 推荐使用虚拟环境：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

首次启动会执行 `Base.metadata.create_all()`，并自动创建默认管理员：

```text
用户名：admin
密码：admin123
```

登录后建议立刻在「个人中心」修改密码。后端 Swagger 位于 [http://localhost:8100/docs](http://localhost:8100/docs)，健康检查位于 [http://localhost:8100/health](http://localhost:8100/health)。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 [http://localhost:5173](http://localhost:5173)。Vite 开发服务器已将 `/api` 代理到 `http://localhost:8100`。如需修改 API 地址，可设置 `VITE_API_BASE`。

生产构建：

```bash
npm run build
npm run preview
```

### 4. 打包 macOS 客户端

桌面端使用 Electron，前端以 Hash 路由运行，避免 `file://` 加载时刷新页面丢失路由。快捷导航、提醒备注中的网址、页面里通过新窗口打开的外部链接，都会交给 macOS 默认浏览器处理；工作台内部页面仍在客户端窗口内切换。

先确认 MySQL 已启动，并在开发机完成后端虚拟环境安装：

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

安装 Electron 打包依赖并启动桌面客户端：

```bash
cd desktop
npm install
npm start
```

`npm start` 会构建桌面版前端并启动 Electron。启动时如果 `8100` 后端已经运行会直接复用；如果当前项目的 `backend/.venv/bin/python` 可用，会尝试自动启动 FastAPI。

生成 macOS 安装包：

```bash
cd desktop
npm run package:mac          # 当前机器架构的 DMG 和 ZIP
npm run package:mac:arm64   # Apple Silicon
npm run package:mac:x64     # Intel Mac
```

安装包输出在 `desktop/dist/`。桌面客户端仍使用本机 MySQL 数据库；要分发给没有 Python 环境的其他 Mac，可先用 PyInstaller 将后端打成 `workbench-api` 可执行文件并放入 `desktop/backend-resources/`，桌面主进程会优先启动它；否则请配置 `WORKBENCH_PYTHON` 或继续让客户端连接一台内网后端服务。

## 功能说明

- 登录体系：bcrypt 密码存储、JWT、前端路由守卫、Axios 自动注入 Token；修改密码或「强制下线所有设备」会递增 `token_version`，立即让旧 Token 失效。
- 个性化设置：主题、侧边栏、默认提醒、默认视图和工作时段写入 `system_config`，同时使用浏览器缓存保证首屏体验。
- 工作记录：列表/日历、日期筛选、关键词检索、标签、工时、编辑删除、Markdown 日报导出。
- 工作计划：起止日期、优先级和状态，支持按月份查看。
- 事件提醒：单次/每日/每周数据结构、延后和关闭；前端每 60 秒轮询到期提醒并调用浏览器通知组件。
- Todo：待处理/进行中/已完成三栏原生拖拽，优先级、截止时间、标签、备注、子任务、批量完成、删除、归档。
- 快捷导航：卡片化链接、分类、编辑删除、点击新标签页打开。
- 数据看板：ECharts 工作量折线、Todo 完成率环图、工具使用频次柱状图及统计卡片。
- 工具箱：JSON、Base64、时间戳、URL 的计算全部在浏览器本地执行；后端 `/api/tools/usage` 只接收使用日志，不处理工具内容。
- 全局检索：统一检索工作记录、计划、待办、快捷链接。
- 公共 UI：提供 `BaseDialog`、`BaseSelect`、`StatusTag` 基础封装，业务页面同时使用 Element Plus 表单/弹窗能力。

## 测试与验证

后端安全函数测试：

```bash
cd backend
pytest -q
```

前端静态构建检查：

```bash
cd frontend
npm run build
```

建议上线前进一步补充：MySQL 集成测试、浏览器通知权限测试、反向代理 HTTPS、JWT 密钥轮换与定期数据库备份。项目不在数据库中保存明文密码，也不会把工具箱输入内容提交给后端。
