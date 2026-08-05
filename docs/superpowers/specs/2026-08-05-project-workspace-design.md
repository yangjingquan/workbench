# 工作区与项目归属设计

## 目标

为工作台增加“工作区 > 项目”两级上下文，将公司工作、个人项目、学习项目隔离，并让工作记录、工作计划、Todo、快捷链接和备忘录可以归属到具体项目。新增项目详情仪表盘，聚合目标、进度、工时、任务、里程碑、版本和提交记录。

## 方案

采用兼容现有数据的增量方案，不重写已有业务表，也不强制旧数据立即归属项目。

### 工作区

`workspace` 表：

- `id`
- `user_id`
- `name`
- `kind`：`company`、`personal`、`learning` 或自定义值
- `color`
- `archived`

默认可创建“公司工作”“个人项目”“学习项目”三个工作区。工作区是用户隔离和项目导航的第一层。

### 项目

`project` 表：

- `id`
- `user_id`
- `workspace_id`
- `name`
- `description`
- `goal`
- `status`：`planning`、`active`、`paused`、`completed`、`archived`
- `tech_stack`：JSON 数组
- `repo_url`
- `local_path`
- `deployment_url`
- `tags`：JSON 数组
- `due_date`
- `archived`

### 项目附属数据

- `project_milestone`：项目里程碑，包含名称、描述、状态、截止日期和排序。
- `project_version`：版本信息，包含版本号、状态、目标日期、发布说明。
- `project_commit`：提交信息，包含哈希、消息、分支、提交时间和链接。第一版支持手动录入，后续再接入 GitHub/GitLab 同步。

### 现有业务归属

为以下表增加可空 `project_id` 外键，删除项目时使用 `SET NULL`：

- `work_record`
- `work_plan`
- `todo_task`
- `quick_link`
- `memo`

查询接口增加可选 `project_id` 过滤；创建和更新接口验证项目属于当前用户。未指定项目时仍允许保存，保证旧客户端和历史数据兼容。

## 历史数据迁移

迁移不猜测历史内容所属场景。为每个用户建立“历史数据”工作区和“未归类项目”，把现有业务记录关联到该项目；用户之后可以从项目管理页手动移动数据。若数据库中没有历史数据，不创建无意义的业务记录。

## 前端交互

新增 `/projects` 项目管理页和 `/projects/:id` 项目详情页。

- 左侧导航增加“项目”。
- 项目页按工作区分组展示项目。
- 顶部提供当前工作区/项目上下文选择器，并保存到 Pinia 和本地缓存。
- 工作记录、计划、Todo、快捷链接、备忘录增加项目筛选。
- 新建内容默认使用当前项目，可在表单中切换项目。
- 项目详情页提供项目资料编辑、里程碑、版本、提交记录和关联数据入口。

## 项目仪表盘

项目详情接口返回聚合数据：

- Todo 总数、已完成数、完成率。
- 投入工时。
- 未完成任务和逾期任务。
- 里程碑完成情况。
- 当前版本和截止日期。
- 最近工作记录。
- 最近提交记录。

聚合统计只查询当前用户且 `project_id` 匹配的数据，避免跨项目和跨用户泄漏。

## API 边界

新增资源接口：

- `/api/workspaces`
- `/api/projects`
- `/api/projects/{id}`
- `/api/projects/{id}/dashboard`
- `/api/projects/{id}/milestones`
- `/api/projects/{id}/versions`
- `/api/projects/{id}/commits`

现有业务接口通过查询参数和请求字段接入 `project_id`，保持已有响应结构不变，仅增加字段。

## 测试与迁移安全

- 模型和接口测试覆盖用户隔离、项目归属校验、历史数据迁移、项目统计聚合。
- 前端契约测试覆盖项目导航、项目筛选、项目表单和仪表盘关键字段。
- 不使用破坏性删除迁移；先补字段和表，再回填历史关联。
- 项目删除默认软删除或解除关联，不直接级联删除工作记录、Todo 和备忘录。
