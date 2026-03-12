# OKX Onchain Assistant

> 参赛作品升级版：把 **OKX OnchainOS 能力 + AI 分析 + 链上执行思路** 打造成一套更像产品、而不是脚本拼盘的 Onchain Copilot。

如果要一句话形容它：

**它不是只会查数据的机器人，而是一套面向链上交易者的 Skills + Workflows 系统。**

---

## 为什么这个版本更能打

这次重构，核心不是多加几个功能，而是把已有能力整理成更清晰的产品结构：

- **7 个独立 Skills**：像 Binance 官方 Skills 一样，职责明确
- **4 个工作流**：Daily Briefing / Deep Dive / On-Chain Intel / Meme Hunter
- **统一专业报告格式**：输出不再像调试日志，更像投研简报
- **更实用的预设 Prompts**：适合 Demo、研究、交易决策
- **环境变量管理 API Key**：避免把比赛项目做成泄密现场

一句话：**更像产品，更适合比赛展示，也更方便后续扩展。**

---

## 亮点能力

### 1. Market Rank：先找到值得看的，再决定值不值得买
- 多链扫描新币
- 条件筛选（流动性 / 市值 / 年龄）
- AI Score 排序
- 快速形成候选池与观察名单

### 2. Token Info：给单个项目建立结构化画像
- 实时价格
- 市值 / Holder / 流动性
- Pool / Heat / 基础面信息
- 适合单币研究和 Demo 展示

### 3. Token Audit：先防死，再谈收益
- 快速审计 owner / mint / blacklist / honeypot 风险
- 输出安全评分与参与建议
- 用统一报告格式展示高风险点

### 4. Trading Signal：把行情、资金流、执行成本拼到一起
- 市场简报
- Smart Money 流向
- 交易计划生成
- 更适合 AI 做“先结论、后理由”的输出

### 5. Spot Execution：把分析变成可执行动作
- 开仓 / 平仓
- 止盈止损
- 仓位计算
- 交易复盘与 PnL 汇总

### 6. Address Info：围绕地址建立链上画像
- 地址近期行为
- 常用 DEX
- 成交量和活动频次
- 授权风险与钱包监控

### 7. Meme Hunter：专门针对高波动机会的捕捉模式
- 新币扫描
- AI Score 排序
- Smart Money 信号辅助
- 审计过滤垃圾项目

---

## 项目结构

```text
okx-onchain-assistant/
├── ai_assistant/              # CLI 助手入口
├── api_server/                # API 服务（可扩展）
├── docs/
│   └── SKILLS.md              # 7 个技能模块设计说明
├── examples/
│   └── workflows.md           # 4 个工作流示例
├── okx_skills/
│   ├── onchainos_api.py       # OKX / Web3 API 封装
│   ├── scan_chain.py          # 多链新币扫描 / Meme Hunter 基础
│   ├── scanner.py             # 扫描器原型
│   ├── audit.py               # 合约快速审计
│   ├── analytics.py           # Holder / Pool / 地址分析
│   ├── security.py            # 授权管理 / 钱包监控 / Gas 预警
│   ├── trading_bot.py         # 仓位与交易执行模拟
│   ├── reporting.py           # 统一专业报告输出
│   └── ai_brain.py            # AI 决策中枢（现有能力）
├── prompts/
│   └── presets.md             # 预设 Prompt 模板
├── screenshots/
├── demo.py                    # 一键演示 Skills + Workflows
├── CONTENT.md
├── CONTENT_V2.md
├── .env.example
└── README.md
```

---

## Skills 视图（参考 Binance 思路）

详细说明见 [`docs/SKILLS.md`](docs/SKILLS.md)。

| Skill | 核心能力 | 适用场景 |
|------|------|------|
| Market Rank | 新币扫描、条件筛选、排名 | 今天先看谁 |
| Token Info | 价格、市值、Holder、池子 | 研究单个 token |
| Token Audit | 蜜罐 / 权限 / 风险筛查 | 下单前排雷 |
| Trading Signal | 市场简报、交易计划、资金流 | 给交易提供信号 |
| Spot Execution | 开仓 / 平仓 / 仓位 / PnL | 把分析变成动作 |
| Address Info | 地址行为、钱包监控、授权风险 | 做链上情报 |
| Meme Hunter | meme 机会发现 + 风险过滤 | 找高弹性标的 |

---

## 4 个工作流

详细示例见 [`examples/workflows.md`](examples/workflows.md)。

### 1) Daily Briefing
适合每天开盘前快速扫一遍市场：
- 看重点币
- 看 Smart Money
- 看新币机会池
- 看 Gas 环境
- 输出今日 watchlist

### 2) Deep Dive
适合研究单个 token：
- Token Info
- Audit
- Holder / Pool / 资金流
- 结构化结论

### 3) On-Chain Intel
适合研究地址和行为：
- 地址活动
- 常用 DEX
- 授权风险
- 是否像聪明钱

### 4) Meme Hunter
适合快速抓热点：
- 扫描新币
- AI Score 排序
- 过滤高风险项目
- 形成 Top Picks / Watchlist / Avoid List

---

## 专业报告输出

新增 `okx_skills/reporting.py`，统一输出：

- 市场简报（Market Brief）
- 新币分析（Token Scan）
- 合约审计（Audit Report）
- 地址画像（Address Report）
- 交易计划（Trade Plan）

这很重要，因为评委和用户看到的不是你内部怎么写代码，而是你**最后怎么呈现判断**。

---

## 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant
pip install -r requirements.txt
```

### 2. 配置环境变量

本项目 **不应硬编码 API Key**。请使用环境变量或 `.env` 文件。

```bash
cp .env.example .env
```

填写：

```bash
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here
OPENCLAW_API_URL=http://127.0.0.1:8080
```

> `.gitignore` 已忽略 `.env`，别把密钥提交上去。比赛想赢，不需要靠自爆。

### 3. 运行演示

```bash
python demo.py
```

### 4. 查看预设 Prompt

```bash
cat prompts/presets.md
```

### 5. 启动 CLI 助手

```bash
python ai_assistant/main.py help
python ai_assistant/main.py market PEPE ethereum
python ai_assistant/main.py plan WETH BUY 1000 ethereum
python ai_assistant/main.py deep WIF solana
```

---

## 示例：输出会长什么样

### 市场简报
```python
from okx_skills.onchainos_api import OnchainOSClient
from okx_skills.reporting import ReportFormatter

client = OnchainOSClient()
price = client.get_price("PEPE", "ethereum")
token = client.search_token("PEPE", "ethereum")
flows = client.get_smart_money_flows("ethereum", "PEPE")

print(ReportFormatter.format_market_brief("PEPE", "ethereum", price, token, flows))
```

### 新币深度分析
```python
from okx_skills.scan_chain import analyze_token
from okx_skills.reporting import ReportFormatter

result = analyze_token(symbol="WIF", chain="solana")
print(ReportFormatter.format_token_scan(result))
```

### 审计报告
```python
from okx_skills.audit import ContractAuditor
from okx_skills.reporting import ReportFormatter

result = ContractAuditor().quick_check("0x742d35Cc6634C0532925a3b844Bc9e7595f", "ethereum")
print(ReportFormatter.format_audit_report(result))
```

---

## 预设 Prompts

见 [`prompts/presets.md`](prompts/presets.md)。

推荐直接拿去做 Demo 的有：
- Daily Briefing
- Deep Dive
- Meme Hunter
- Address Intel
- Trade Plan
- PM / Demo 模式

这些 Prompt 的目标只有一个：

**让 AI 输出像研究员，不像终端报错信息。**

---

## Demo 建议打法

如果你只有 3~5 分钟向评委展示，最建议的顺序是：

1. **Daily Briefing** —— 先展示产品感
2. **Deep Dive** —— 再展示分析深度
3. **Meme Hunter** —— 最后展示链上速度感和机会发现能力

这套顺序非常稳：
- 有结构
- 有数据
- 有 AI
- 有执行想象空间

---

## 安全说明

- API Key 仅通过环境变量读取
- `.env` 已加入 `.gitignore`
- 代码中默认避免硬编码敏感信息
- 交易与执行功能当前以演示 / 模拟为主，接真实执行前应补充签名、安全校验与权限控制

---

## 当前版本升级点

### v4.0
- 按 Binance Skills 思路重构为 **7 Skills + 4 Workflows**
- 新增 `docs/SKILLS.md`
- 新增 `examples/workflows.md`
- 新增 `prompts/presets.md`
- 新增 `okx_skills/reporting.py` 统一专业报告格式
- 升级 `demo.py`，更适合比赛演示
- 优化 CLI 输出，支持 `market` / `plan` / `deep`
- 强化环境变量与安全说明

---

## GitHub

<https://github.com/0xUnite/okx-onchain-assistant>
