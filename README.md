# Prompt 工厂基座

根据配置，批量产出**高度拟人、不重复、无模板痕迹**的评测用 Prompt。提供 REST API + Web 前端管理界面，**不包含**任何评测业务逻辑。

## 界面预览

<table>
  <tr>
    <td align="center"><b>仪表盘</b></td>
    <td align="center"><b>项目管理</b></td>
  </tr>
  <tr>
    <td><img src="docs/img/01.png" alt="仪表盘" width="480" /></td>
    <td><img src="docs/img/02.png" alt="项目管理" width="480" /></td>
  </tr>
  <tr>
    <td align="center"><b>人格管理</b></td>
    <td align="center"><b>模板管理</b></td>
  </tr>
  <tr>
    <td><img src="docs/img/04.png" alt="人格管理" width="480" /></td>
    <td><img src="docs/img/05.png" alt="模板管理" width="480" /></td>
  </tr>
  <tr>
    <td align="center"><b>后处理规则</b></td>
    <td align="center"><b>模型管理</b></td>
  </tr>
  <tr>
    <td><img src="docs/img/06.png" alt="后处理规则" width="480" /></td>
    <td><img src="docs/img/07.png" alt="模型管理" width="480" /></td>
  </tr>
</table>

## 核心架构

### 基座分层

所有配置型数据遵循 **公共资源 → 项目级资源** 两层继承覆盖：

```
最终生效集合 = 公共条目 ∪ 项目专属条目（同名覆盖）
```

适用于：人格特征、元提示模板、后处理规则、模型配置。

### 生成流水线

```
人格装配 → 元提示生成 → LLM 调用 → 后处理管线 → 去重检查 → 存储
```

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.11+ / FastAPI / Pydantic v2 / SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 + pgvector（向量存储 + 业务数据统一） |
| 前端 | Vue 3 / TypeScript / Element Plus / Vite |
| 部署 | Docker / docker-compose（单体部署，前端由 FastAPI 托管） |

## 功能特性

- **人格装配器** — 6 个维度加权随机抽取，公共/项目两级继承
- **元提示模板** — 变量插值 + 随机约束，永不重复的 system prompt
- **15+ LLM 厂商** — OpenAI / Anthropic / Azure / Bedrock / DeepSeek / Kimi / 百炼 / 硅基流动 / 豆包 / 文心一言 / 腾讯混元 / MiniMax / 阶跃星辰 / 零一万物 / 智谱 / Gemini / Mistral / Meta
- **API Key 加密存储** — 前端填写 Key，后端 Fernet 加密存库，无需配置环境变量
- **7 条后处理规则** — 模拟人类打字习惯，受 human_likeness 倍率控制
- **pgvector 去重** — 余弦相似度检索，可配置阈值
- **SSE 实时进度** — 异步生成 + Server-Sent Events 推送
- **Glassmorphism UI** — 玻璃拟态暗色主题管理界面
- **雪花算法 ID** — 项目 ID 采用 Snowflake 算法自动生成

## 快速开始

### Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/<your-username>/prompt-factory.git
cd prompt-factory

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入数据库连接串和 SECRET_KEY

# 3. 启动服务
docker-compose up -d

# 4. 访问
# 前端：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑填入配置
uvicorn main:app --reload --port 8000

# 前端（开发模式）
cd frontend
npm install
npm run dev  # http://localhost:5173

# 前端（构建并部署到后端）
npm run build
cp -r dist/* ../backend/app/static/
```

### 数据库初始化

```bash
# 使用 SQL 脚本（建库 + 建表 + 种子数据，一键完成）
psql -U <user> -d prompt_factory -f docs/sql/init.sql
```

种子数据包含：
- 101 条公共人格特征（覆盖 6 个 category：occupation/mood/language_habit/typing_habit/scene/education）
- 6 套公共元提示模板
- 7 条公共后处理规则
- 18 个模型配置（仅 DeepSeek 默认启用，其余需在前端填写 API Key 后启用）

## 项目结构

```
prompt-factory/
├── backend/
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.yaml              # 全局运行配置
│   ├── requirements.txt         # Python 依赖
│   ├── .env.example             # 环境变量模板
│   ├── app/
│   │   ├── api/                 # API 路由
│   │   │   ├── projects.py      # 项目管理
│   │   │   ├── generate.py      # 生成相关
│   │   │   ├── personas.py      # 人格特征管理
│   │   │   ├── templates.py     # 元提示模板管理
│   │   │   ├── postprocess.py   # 后处理规则管理
│   │   │   ├── models.py        # 模型配置管理
│   │   │   └── history.py       # 历史记录 + 健康检查
│   │   ├── models/              # ORM 模型 + Pydantic Schema
│   │   ├── services/            # 业务逻辑
│   │   │   ├── persona.py       # 人格装配器
│   │   │   ├── generator.py     # 元提示生成器
│   │   │   ├── postprocess.py   # 后处理管线
│   │   │   ├── dedup.py         # 去重引擎
│   │   │   └── llm_provider.py  # LLM 提供者抽象（4 种 Provider）
│   │   ├── core/                # 基础设施
│   │   │   ├── config.py        # 配置加载
│   │   │   ├── crypto.py        # Fernet 加密/解密/脱敏
│   │   │   ├── database.py      # 数据库连接
│   │   │   ├── snowflake.py     # 雪花算法 ID 生成器
│   │   │   └── exceptions.py    # 异常处理
│   │   └── static/              # 前端构建产物
│   └── tests/                   # 单元测试
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── components/          # 业务组件
│   │   ├── api/                 # API 封装
│   │   ├── stores/              # Pinia 状态管理
│   │   └── router/              # 路由配置
│   └── package.json
├── docs/
│   ├── sql/
│   │   └── init.sql             # 完整建库建表 + 种子数据脚本（含中文注释）
│   └── img/                     # 运行截图
├── persona_bank.yaml            # 人格特征种子数据源
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml
└── .gitignore
```

## API 接口

### 生成相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/generate` | 同步批量生成 Prompt |
| POST | `/api/v1/generate/async` | 异步生成（返回 task_id） |
| GET | `/api/v1/generate/{task_id}` | 查询异步任务状态 |
| GET | `/api/v1/generate/{task_id}/stream` | SSE 实时进度推送 |
| GET | `/api/v1/history/{project_id}` | 查询生成历史 |
| DELETE | `/api/v1/project/{project_id}` | 删除项目所有 Prompt |

### 项目管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/projects` | 列出所有项目 |
| POST | `/api/v1/projects` | 创建项目（ID 自动生成雪花算法） |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| PUT | `/api/v1/projects/{id}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | 删除项目（级联） |

### 人格特征

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/persona/traits` | 查询人格特征（支持 category/offset/limit 分页） |
| POST | `/api/v1/persona/traits` | 新增人格特征 |
| PUT | `/api/v1/persona/traits/{id}` | 修改人格特征 |
| DELETE | `/api/v1/persona/traits/{id}` | 删除人格特征 |
| POST | `/api/v1/persona/traits/import` | 批量导入 |
| GET | `/api/v1/persona/preview/{project_id}` | 预览合并后人格库 |

### 元提示模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/meta-templates` | 查询模板列表（支持 offset/limit 分页） |
| POST | `/api/v1/meta-templates` | 新增模板 |
| PUT | `/api/v1/meta-templates/{id}` | 修改模板 |
| DELETE | `/api/v1/meta-templates/{id}` | 删除模板 |

### 后处理规则

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/postprocess/rules` | 查询规则列表（支持 offset/limit 分页） |
| POST | `/api/v1/postprocess/rules` | 新增规则 |
| PUT | `/api/v1/postprocess/rules/{id}` | 修改规则 |
| DELETE | `/api/v1/postprocess/rules/{id}` | 删除规则 |
| PUT | `/api/v1/postprocess/rules/sort` | 批量调整排序 |

### 模型配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/models` | 查询模型配置（支持 offset/limit 分页） |
| POST | `/api/v1/models` | 新增模型配置 |
| PUT | `/api/v1/models/{id}` | 修改模型配置 |
| DELETE | `/api/v1/models/{id}` | 删除模型配置 |
| POST | `/api/v1/models/{id}/test` | 测试模型连通性 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 服务健康检查 |

## API 调用示例

### 创建项目

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "医疗咨询评测",
    "description": "针对医疗咨询场景的 prompt 生成",
    "config": {
      "similarity_threshold": 0.87,
      "human_likeness": "high",
      "source_models": ["deepseek-chat", "glm-4-flash"]
    }
  }'
```

### 同步生成 Prompt

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "task_domain": "医疗咨询",
    "count": 10,
    "human_likeness": "high",
    "source_models": ["deepseek-chat"],
    "similarity_threshold": 0.87
  }'
```

### 异步生成 + SSE 进度

```bash
# 提交异步任务
curl -X POST http://localhost:8000/api/v1/generate/async \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_id>",
    "task_domain": "医疗咨询",
    "count": 50,
    "human_likeness": "high"
  }'

# 监听 SSE 进度
curl -N http://localhost:8000/api/v1/generate/{task_id}/stream
```

### 查询生成历史

```bash
curl "http://localhost:8000/api/v1/history/<project_id>?limit=20&offset=0"
```

## 核心功能说明

### 人格装配器

从数据库查询公共 + 项目专属人格特征，按 `(category, label)` 合并去重（项目级覆盖公共级），对每个 category 加权随机抽取 1-3 项，组装成 `Persona` 对象。

6 个 category：`occupation`、`mood`、`language_habit`、`typing_habit`、`scene`、`education`

### 元提示生成器

从模板池中加权随机选取模板，用 `{{role}}`、`{{scene}}`、`{{mood}}`、`{{quirk}}`、`{{domain}}`、`{{descriptions}}` 等变量插值，附加随机约束（错别字数量、句式要求、额外指令），生成永不重复的 system prompt。

### 后处理管线

7 条内置规则，按 `sort_order` 依次执行，每条规则有独立概率，受 `human_likeness` 全局倍率控制：

| 规则 | 说明 |
|------|------|
| `prefix_filler` | 开头插入填充词 |
| `replace_de` | "的" → "滴" |
| `randomize_punctuation` | 标点随机替换/删除 |
| `insert_filler_words` | 插入语气词 |
| `lowercase_start` | 句首大写变小写 |
| `mess_spacing` | 中英文间距错乱 |
| `remove_punctuation` | 随机删除标点 |

`human_likeness` 倍率：`low=0.3` / `medium=0.6` / `high=1.0` / `insane=1.5`

### 去重引擎

使用 pgvector 余弦相似度检索，默认阈值 0.85。超过阈值则丢弃并重试（最多 5 次）。Embedding API 失败时降级为跳过去重（标记 `dedup_skipped=true`），避免阻塞生成流程。

### LLM 提供者

4 种 Provider 类型，覆盖 15+ 厂商：

| Provider 类型 | 适用厂商 |
|---|---|
| `openai` | OpenAI / DeepSeek / Kimi / 百炼 / 硅基流动 / 豆包 / 文心一言 / 腾讯混元 / MiniMax / 阶跃星辰 / 零一万物 / 智谱 / Gemini / Mistral / Meta |
| `anthropic` | Anthropic (Claude 原生 API) |
| `azure` | Azure OpenAI |
| `bedrock` | Amazon Bedrock |

### API Key 安全机制

- API Key 通过前端管理页面填写，**不存储明文**
- 使用 Fernet 对称加密（AES-128-CBC + HMAC-SHA256）存入数据库 `api_key_encrypted` 字段
- 加密密钥由 `SECRET_KEY` 配置项 + SHA-256 派生
- API 响应仅返回脱敏格式（如 `sk-0****6fa4`），永远不返回明文
- 无需在 `.env` 中配置任何 API Key

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://pf_user:password@localhost:5432/prompt_factory` |
| `SECRET_KEY` | API Key 加密密钥（生产环境务必修改） | `change-me-in-production-use-a-random-string` |

完整配置见 `config.yaml` 和 `backend/.env.example`。

## 测试

```bash
cd backend
pytest tests/ -v
```

测试覆盖：人格装配器、后处理管线、元提示生成、去重引擎、API 端点。

## License

MIT License
