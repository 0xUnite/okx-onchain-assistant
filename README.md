# OKX OnchainOS AI Assistant

> 🦞 参赛作品 | OKX OnchainOS AI 松  
> 基于 OpenClaw + OKX OnchainOS Skills 打造的链上 AI 交易助手

---

## 项目亮点

这不是普通的链上看盘工具，而是一个 **会分析、会决策、会执行** 的 AI 交易助手。

### 🤖 AI 网格策略
AI 持续分析市场波动率、趋势强弱与流动性状态，**自动设置最优网格区间、层数、间距与仓位分配**，减少手动调参。

### 📰 新闻情绪交易
实时抓取新闻、社媒与热点事件，结合 AI 做情绪分析，识别利多/利空信号，**自动触发交易执行或风险减仓**。

### 🐋 鲸鱼跟单
追踪聪明钱地址、鲸鱼钱包与链上大额异动，识别高价值买卖动作，结合 OKX 交易能力实现 **一键跟单 / 快速复制策略**。

### 📊 智能止盈止损
AI 根据实时波动率、市场结构和持仓状态，**动态调整止盈止损位置**，避免固定参数在剧烈行情中失效。

---

## 技术架构

```text
okx-onchain-assistant/
├── okx_skills/              # 核心策略与链上能力
│   ├── onchainos_api.py     # OKX / OnchainOS API 封装
│   ├── scanner.py           # 新币扫描 + AI 评分
│   ├── audit.py             # 合约审计
│   ├── analytics.py         # Holder / 池子 / 热度分析
│   ├── security.py          # 授权管理 + Gas 预警
│   ├── monitor.py           # 链上监控 / 套利 / 异常检测
│   ├── trading_bot.py       # 自动交易机器人
│   └── ai_brain.py          # AI 决策中枢 / 回测 / 风控
├── web_ui/                  # Web 仪表盘
│   └── main.py
├── ai_assistant/            # CLI 对话助手
│   └── main.py
├── demo.py                  # 演示脚本
├── CONTENT.md               # 参赛提交内容
├── CONTENT_V2.md            # 备用内容版本
└── requirements.txt         # 项目依赖
```

---

## 核心能力地图

### 1. AI 交易决策层
- **AI 网格策略**：基于波动率、趋势、流动性自动生成网格参数
- **智能止盈止损**：根据行情波动动态调整 TP / SL
- **策略回测**：对 AI 决策进行历史回测与效果验证
- **仓位管理**：结合风险评分控制开仓比例与暴露水平

### 2. 信息感知层
- **新闻情绪交易**：抓取新闻、社媒、事件流并做情绪判断
- **新币扫描**：监控多链新币，AI 评分筛选优质机会
- **链上热点分析**：识别代币热度、池子变化和异常活跃地址
- **鲸鱼跟单**：跟踪聪明钱地址和大额资金异动

### 3. 执行与安全层
- **自动交易执行**：支持开仓、平仓、止盈止损管理
- **合约审计**：检测蜜罐、增发、黑名单、流动性风险
- **授权管理**：发现高风险授权并支持一键撤销
- **Gas / 风险监控**：优化交易时机，降低执行损耗

---

## 模块说明

| 模块 | 作用 |
|------|------|
| `ai_brain.py` | AI 决策中枢，负责策略生成、情绪分析、回测、动态风控 |
| `trading_bot.py` | 自动执行交易、管理仓位、联动止盈止损 |
| `monitor.py` | 链上异常监控、套利发现、资金异动识别 |
| `analytics.py` | Holder 结构、池子深度、热度与地址行为分析 |
| `scanner.py` | 新币扫描、项目评分、机会发现 |
| `audit.py` | 合约安全检查，防 Rug / 蜜罐 / 黑名单 |
| `security.py` | 授权管理、钱包风险监控、Gas 预警 |
| `onchainos_api.py` | 对接 OKX OnchainOS / 交易与链上能力 |

---

## 快速开始

```bash
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant
pip install -r requirements.txt

# 运行演示
python demo.py

# 启动 Web UI
python web_ui/main.py

# 启动 CLI 助手
python ai_assistant/main.py
```

---

## 场景示例

### AI 网格策略
```python
from okx_skills.ai_brain import backtest_strategy

result = backtest_strategy("AI_GRID", "ETH", 30)
print(result)
```

### 新闻情绪交易
```python
from okx_skills.ai_brain import ai_decide

signal = {
    "token": "BTC",
    "news_sentiment": "bullish",
    "volatility": "high",
    "event": "ETF inflow"
}
market = {
    "trend": "up",
    "rsi": 62,
    "liquidity": "good"
}

print(ai_decide(signal=signal, market=market))
```

### 鲸鱼跟单
```python
from okx_skills.analytics import analyze_holders

result = analyze_holders("PEPE", "ethereum")
print(result)
```

### 智能止盈止损
```python
from okx_skills.trading_bot import open_position

result = open_position(
    token="ETH",
    chain="ethereum",
    side="LONG",
    entry_price=3000,
    quantity=0.1,
    stop_loss=2880,
    take_profit=3300
)
print(result)
```

---

## CLI 示例

```bash
python ai_assistant/main.py scan
python ai_assistant/main.py search PEPE
python ai_assistant/main.py audit 0x742d...
python ai_assistant/main.py buy ETH 0.1
python ai_assistant/main.py portfolio 0x...
```

---

## 环境变量

```bash
export OKX_API_KEY="your-key"
export OKX_SECRET_KEY="your-secret"
export OKX_PASSPHRASE="your-passphrase"
export FLASK_ENV=development
```

---

## Changelog

### v3.1 (2026-03-10)
- 突出 AI 网格策略、新闻情绪交易、鲸鱼跟单、智能止盈止损
- 重构 README 结构，强化产品卖点表达
- 更新参赛内容文档

### v3.0 (2026-03-08)
- AI 独有能力：24/7 监控、多链监控、情绪管理
- 策略回测、异常检测、社交监听

### v2.2 (2026-03-08)
- 授权管理、Gas 预警、钱包监控
- 套利扫描、新池子监控、闪电贷检测

### v2.1 (2026-03-08)
- Holder 分析、池子分析、代币热度
- 交易机器人、跨链桥

### v1.0 (2026-03-07)
- 初始版本

---

## GitHub

https://github.com/0xUnite/okx-onchain-assistant
