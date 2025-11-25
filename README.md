# ZotWatch

ZotWatch 是一个基于 Zotero 数据构建个人兴趣画像，并持续监测学术信息源的新文献推荐流程。它可以在本地手动执行，也可以每日在 GitHub Actions 上自动运行，将最新候选文章生成 RSS/HTML 报告。

## 功能概览
- **Zotero 同步**：通过 Zotero Web API 获取文库条目，增量更新本地画像。
- **画像构建**：对条目向量化，提取高频作者/期刊，并记录近期热门期刊。
- **候选抓取**：拉取 Crossref、arXiv、bioRxiv/medRxiv（可选）等数据源，并对热门期刊做额外精准抓取。
- **去重打分**：结合语义相似度、时间衰减、引用/Altmetric、SJR 期刊指标及白名单加分生成推荐列表。
- **输出发布**：生成 `reports/feed.xml` 供 RSS 订阅，并通过 GitHub Pages 发布；同样可生成 HTML 报告或推送回 Zotero。

## 快速开始

### 1. 克隆仓库并安装依赖
```bash
git clone <your-repo-url>
cd ZotWatch
uv sync
```

### 2. 获取 Zotero API 凭证
- `ZOTERO_API_KEY`：登录 [Zotero 个人账户](https://www.zotero.org/settings/)，在 **Settings - Security - Applications** 处点击 **Create new private key**，Personal Library 给予 Allow library access，Default Group Permissions 给予 Read Only 权限。
- `ZOTERO_USER_ID`：在上述页面 **Create new private key** 按钮下方可见 `Your user ID for use in API calls is ******`。

### 3. 配置环境变量
在仓库根目录创建 `.env` 文件：
```bash
ZOTERO_API_KEY=your_api_key_here
ZOTERO_USER_ID=your_user_id_here
# 可选
OPENALEX_MAILTO=you@example.com
CROSSREF_MAILTO=you@example.com
ALTMETRIC_KEY=your_altmetric_key
```

### 4. 运行
```bash
# 首次全量画像构建
uv run python -m src.cli profile --full

# 日常监测（生成 RSS + HTML）
uv run python -m src.cli watch --rss --report --top 20
```

## GitHub Actions 自动运行

如果你希望每日自动运行并通过 GitHub Pages 发布 RSS，可以 Fork 本仓库并配置 GitHub Actions：

### 1. Fork 仓库
打开 [ZotWatch](https://github.com/Yorks0n/ZotWatch)，点击 **Fork** 按钮。

### 2. 配置 Secrets
在 Fork 后的仓库中，进入 **Settings → Secrets and variables → Actions**，点击 **New repository secret** 添加：
- `ZOTERO_API_KEY`
- `ZOTERO_USER_ID`
- `OPENALEX_MAILTO`（邮箱地址）
- `CROSSREF_MAILTO`（邮箱地址）

### 3. 启用 GitHub Pages
进入 **Settings → Pages**，将 **Source** 设置为 **GitHub Actions**。

### 4. 启用 Workflow
进入 **Actions** 栏目，点击 **Daily Watch & RSS**，然后点击 **Enable workflow** 激活。

### 5. 运行与访问
- Workflow 默认每天北京时间 6:05 自动运行，也可手动点击 **Run workflow** 立即执行。
- 首次运行需要全量生成向量数据库，耗时较长。
- 运行完成后，RSS 地址为：`https://[username].github.io/ZotWatch/feed.xml`

## 目录结构
```
├─ src/                   # 主流程模块
├─ config/                # YAML 配置，含 API 及评分权重
├─ data/                  # 画像/缓存/指标文件（不纳入版本控制）
├─ reports/               # 生成的 RSS/HTML 输出
└─ .github/workflows/     # GitHub Actions 配置
```

## 自定义配置
- `config/zotero.yaml`：Zotero API 参数（`user_id` 可写 `${ZOTERO_USER_ID}`，将由 `.env`/Secrets 注入）。
- `config/sources.yaml`：各数据源开关、分类、窗口大小（默认 7 天）。
- `config/scoring.yaml`：相似度、期刊质量等权重；并提供手动白名单支持。

## 常见问题
- **缓存过旧**：候选列表默认缓存 12 小时，可删除 `data/cache/candidate_cache.json` 强制刷新。
- **未找到热门期刊补抓**：确保已运行过 `profile --full` 生成 `data/profile.json`。
- **推荐为空**：检查是否所有候选都超出 7 天窗口或预印本比例被限制；可调节 CLI 的 `--top`、`_filter_recent` 的天数或 `max_ratio`。
