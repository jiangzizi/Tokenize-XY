# Tokenized-XY 项目

## 项目背景

本项目旨在对清华大学新雅书院进行"token化"处理，将书院公众号的全部文章内容转化为可用于AI训练和分析的结构化数据。

## 数据来源

- 公众号：清华大学新雅书院
- 数据位置：`data/`
  - `official_account_menu_lite.json`：轻量版数据（3篇，用于debug）
  - `official_account_menu.json`：完整版数据（1,124篇）

## 数据格式

每篇文章包含以下字段：
- `aid`：文章唯一标识
- `title`：标题
- `digest`：摘要
- `link`：原文链接
- `cover`：封面图URL
- `create_time`/`update_time`：创建/更新时间（Unix时间戳）
- `album_id`：所属专辑ID
- `appmsg_album_infos`：专辑信息
- `content`：文章内容（需另行抓取）
- `comments`：评论（需另行抓取）

## 开发环境

- **Conda环境**：`tokenized_xy`
- 所有开发工作必须在此conda环境下进行

## 项目结构

```
src/
├── menu_lens/                    # 核心分析模块
│   ├── __init__.py
│   ├── loader.py                 # 数据加载器
│   ├── analyzer.py               # 数据分析器（jieba分词）
│   ├── stats.py                  # 报告生成器
│   └── dashboard/                # CLI可视化面板
│       ├── __init__.py
│       ├── app.py               # 交互式/静态面板应用
│       └── panels.py            # 面板组件（4个标签页）
└── menu_lens_demo.py            # 演示脚本

scripts/
├── menu_lens.sh                 # 基础分析脚本
└── menu_dashboard.sh            # 交互式面板脚本

reports/                         # 生成的分析报告
```

## 已完成工作

### 1. Menu Lens 分析模块 (`src/menu_lens/`)

**Loader (`loader.py`)**：
- JSON数据加载与验证
- Unix时间戳自动转换为datetime
- 按专辑分组查询
- 时间范围筛选

**Analyzer (`analyzer.py`)**：
- 使用`jieba`进行专业中文分词
- 停用词过滤（机构名、虚词、数字等）
- 自定义词典（新雅书院、南十北、通识教育等）
- 分析维度：
  - 标题：长度分布、高频关键词、系列文章识别
  - 摘要：覆盖率、关键词提取
  - 时间：年份/月份/星期/时段分布
  - 专辑：栏目统计、时间跨度

**Stats (`stats.py`)**：
- 生成文本格式报告
- 生成JSON格式报告
- 控制台摘要打印

### 2. CLI Dashboard (`src/menu_lens/dashboard/`)

基于`rich`库构建的现代化CLI可视化面板：

| 面板 | 内容 |
|------|------|
| **📊 概览** | 大数字卡片（文章数、栏目数、系列文章、运营天数） |
| **📅 时间线** | 年份/月份/星期/时段分布条形图 |
| **🔑 关键词** | 标题/摘要高频词Top 15，带可视化条形 |
| **📁 栏目** | 栏目排行表格、时间跨度、趋势图 |

**使用方式**：
```bash
# 交互式模式（需在真实终端运行）
bash scripts/menu_dashboard.sh

# 静态模式（直接输出所有面板）
bash scripts/menu_dashboard.sh --static

# 使用轻量数据
bash scripts/menu_dashboard.sh --lite
```

### 3. 数据洞察（1,124篇文章）

- **时间跨度**：2016-05-22 ~ 2026-04-07（3,607天，近10年）
- **栏目数**：83个
- **发布规律**：工作日集中发布（周一~周四占76%），周末较少
- **主要栏目**：
  - 未分类（618篇，55%）
  - 新雅南十北·惊鸿系列（129篇）
  - 南十北·从游计划·聚谈（51篇）
- **高频关键词**：南十北、惊鸿、实践、学术、聚谈、活动

## 依赖包

```bash
pip install jieba rich textual
```

## 项目目标

1. ✅ 清洗和解析公众号文章metadata
2. ✅ 构建数据分析模块（menu_lens）
3. ✅ 构建CLI可视化面板
4. ⬜ 抓取文章内容（目前只有metadata）
5. ⬜ 将文本内容token化，生成训练数据集
6. ⬜ 构建适用于AI模型的结构化数据

## 注意事项

- 文章目前只有metadata，`content`字段为空，需要后续抓取
- 部分文章属于专辑（如"新雅南十北·惊鸿系列"、"暑期项目"等）
- 注意处理时间戳转换（Unix时间戳 -> 可读时间）
- Dashboard交互模式需要在真实终端运行，非TTY环境自动回退到静态模式
