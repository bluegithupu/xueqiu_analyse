# Capability: crawl-mode

爬虫内容来源配置

## ADDED Requirements

### Requirement: 配置项定义

系统 SHALL 支持 `settings.yaml` 中的 `crawl.mode` 配置：
- `column`（默认）：仅保存长文（有标题或 mark>=1 的文章）
- `timeline`：保存所有动态

#### Scenario: 默认配置

**Given** 配置文件无 `crawl.mode` 设置  
**When** 执行抓取任务  
**Then** 仅保存 `type=long_post` 的文章

#### Scenario: 全量模式

**Given** 配置 `crawl.mode: timeline`  
**When** 执行抓取任务  
**Then** 保存所有类型内容（`long_post` 和 `short_status`）

---

### Requirement: 命令行参数覆盖

`crawl_user.py` SHALL 支持 `--mode` 参数覆盖配置文件设置。

#### Scenario: 命令行指定 timeline

**Given** 配置文件 `crawl.mode: column`  
**When** 执行 `python scripts/crawl_user.py Blue7az --mode timeline`  
**Then** 抓取所有类型内容

---

### Requirement: 长文判定逻辑

系统 SHALL 将满足以下任一条件的文章判定为长文：
- `mark == 1`
- 存在非空 `title`

#### Scenario: 有标题的文章

**Given** 文章数据 `{"title": "投资随想", "mark": 0}`  
**When** 判定文章类型  
**Then** 类型为 `long_post`

#### Scenario: mark 标记的长文

**Given** 文章数据 `{"title": "", "mark": 1}`  
**When** 判定文章类型  
**Then** 类型为 `long_post`

