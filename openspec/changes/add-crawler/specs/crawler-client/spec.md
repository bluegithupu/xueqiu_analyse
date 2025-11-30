## ADDED Requirements

### Requirement: HTTP 客户端初始化

系统 SHALL 提供 `XueqiuClient` 类，从配置文件加载 cookies、User-Agent 和请求参数。

#### Scenario: 成功加载配置
- **WHEN** 配置文件 `config/cookies.json` 和 `config/settings.yaml` 存在且有效
- **THEN** 客户端成功初始化，Session 携带正确的 cookies 和 headers

#### Scenario: cookies 文件缺失
- **WHEN** `config/cookies.json` 不存在
- **THEN** 抛出 `FileNotFoundError`，提示用户创建配置文件

### Requirement: JSON 请求

系统 SHALL 提供 `get_json(url, params)` 方法，发送 GET 请求并返回解析后的 JSON 对象。

#### Scenario: 正常响应
- **WHEN** 请求返回 200 且 Content-Type 为 JSON
- **THEN** 返回解析后的 dict/list

#### Scenario: 非 JSON 响应
- **WHEN** 响应不是有效 JSON
- **THEN** 抛出 `ValueError`

### Requirement: HTML 请求

系统 SHALL 提供 `get_html(url, params)` 方法，发送 GET 请求并返回 HTML 文本。

#### Scenario: 正常响应
- **WHEN** 请求返回 200
- **THEN** 返回 HTML 字符串

### Requirement: 请求限速

系统 SHALL 在每次请求后等待配置的时间间隔，默认 1-2 秒随机。

#### Scenario: 连续请求
- **WHEN** 连续调用两次请求方法
- **THEN** 第二次请求在第一次完成后至少等待配置的最小间隔时间

### Requirement: 请求重试

系统 SHALL 对 5xx 错误和网络异常进行指数退避重试，最多重试 3 次。

#### Scenario: 临时服务器错误
- **WHEN** 首次请求返回 503，重试时返回 200
- **THEN** 返回成功响应

#### Scenario: 持续失败
- **WHEN** 连续 4 次请求都失败
- **THEN** 抛出最后一次的异常

### Requirement: Cookies 失效检测

系统 SHALL 检测响应是否被重定向到登录页，若是则抛出 `CookiesExpiredError`。

#### Scenario: 登录页重定向
- **WHEN** 响应 URL 包含登录页路径（如 `/login`）
- **THEN** 抛出 `CookiesExpiredError`，提示用户更新 cookies
