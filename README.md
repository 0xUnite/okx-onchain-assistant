# OKX OnchainOS AI Assistant

> 🦞 参赛作品 | OKX OnchainOS AI 松

基于 OpenClaw + OKX OnchainOS Skills 开发的链上 AI 交易助手。

---

## 技术架构

```
okx-onchain-assistant/
├── okx_skills/              # 核心模块
│   ├── onchainos_api.py     # OKX API 封装
│   ├── scanner.py           # 新币扫描 + AI 评分
│   ├── audit.py            # 合约审计
│   ├── analytics.py        # Holder/池子/热度分析
│   ├── security.py         # 授权管理 + Gas 预警
│   ├── monitor.py          # 套利扫描 + 闪电贷检测
│   ├── trading_bot.py      # 自动交易机器人
│   ├── trade_guard.py      # 交易前体检 + 大单拆单
│   └── ai_brain.py        # AI 决策 + 回测
├── web_ui/                  # Web 仪表盘
├── ai_assistant/            # CLI 对话
└── demo.py                  # 演示脚本
```

---

## 核心功能

### 交易核心

| 模块 | 功能 |
|------|------|
| `scanner.py` | 新币监控、AI 评分 (≥85 推送)、合约审计 |
| `audit.py` | 流动性检测、增发/黑名单扫描、蜜罐识别 |
| `trading_bot.py` | 自动开仓/平仓、止盈止损、仓位管理 |
| `onchainos_api.py` | 钱包余额、DEX 闪兑、跨链桥 |
| `trade_guard.py` | 下单前体检（滑点/Gas/安全/授权）+ 大单拆单计划 |

### 链上分析

| 模块 | 功能 |
|------|------|
| `analytics.py` | Holder 分布、池子深度、代币热度、地址追踪 |
| `monitor.py` | 套利扫描、新池子监控、闪电贷检测 |
| `security.py` | Token 授权管理、一键撤销、钱包监控 |

### AI 增强

| 模块 | 功能 |
|------|------|
| `ai_brain.py` | AI 交易决策、情绪管理、策略回测 |
| | 多链监控 (20+ 链)、异常模式识别 |
| | 社交监听 (Twitter/TG/Discord) |

---

## 快速开始

```bash
# 克隆
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant

# 安装
pip install -r requirements.txt

# 运行演示
python demo.py

# 查看提示词
python demo.py prompts

# 启动 Web
python web_ui/main.py

# CLI 助手
python ai_assistant/main.py
```

---

## 模块详解

### 1. 新币扫描 + AI 评分

```python
from okx_skills.scanner import NewTokenScanner

scanner = NewTokenScanner()
tokens = scanner.scan_chain("ethereum")

for token in tokens:
    analysis = scanner.analyze_token(token)
    print(f"Score: {analysis['score']} - {analysis['recommendation']}")
```

### 2. 合约审计

```python
from okx_skills.audit import audit_contract

result = audit_contract("0x742d...", "ethereum")
print(f"安全分数: {result['score']}/100")
print(f"建议: {result['recommendation']}")
```

### 3. 交易机器人

```python
from okx_skills.trading_bot import open_position, close_position, get_positions

# 开仓
result = open_position(
    token="WETH",
    chain="ethereum",
    side="LONG",
    entry_price=3000,
    quantity=0.1,
    stop_loss=2850,
    take_profit=3300
)

# 平仓
close_position("1", 3150, "TP")

# 查看仓位
positions = get_positions("OPEN")
```

### 4. Holder 分析

```python
from okx_skills.analytics import analyze_holders

result = analyze_holders("PEPE", "ethereum")
print(f"Top10 集中度: {result['top10_concentration']}%")
print(f"风险等级: {result['risk_level']}")
```

### 5. 授权管理

```python
from okx_skills.security import check_approvals

result = check_approvals("0x742d...", "ethereum")
print(f"风险分数: {result['risk']['risk_points']}")
print(f"风险等级: {result['risk']['risk_level']}")
```

### 6. AI 决策

```python
from okx_skills.ai_brain import ai_decide

decision = ai_decide(
    signal={"token": "ETH"},
    market={"rsi": 85, "sentiment": "extreme_greed", "trend": "up"}
)
print(f"决策: {decision['decision']}")
print(f"信心度: {decision['confidence']}%")
```

### 7. 策略回测

```python
from okx_skills.ai_brain import backtest_strategy

result = backtest_strategy("趋势跟踪", "ETH", 30)
print(f"胜率: {result['win_rate']}%")
print(f"总盈亏: {result['total_pnl_pct']}%")
```

### 8. 交易前体检 + 拆单

```python
from okx_skills.trade_guard import pre_trade_check, plan_order_slices

check = pre_trade_check("ETH", "USDC", 1, chain="ethereum", wallet_address="0x742d...")
print(check["decision"], check["risk_score"])

plan = plan_order_slices("ETH", "USDC", 50, chain="ethereum")
print(plan["recommended_slices"], plan["estimated_slice_impact_pct"])
```

---

## CLI 命令

```bash
# 查余额
python ai_assistant/main.py portfolio 0x...

# 查价格
python ai_assistant/main.py price ETH

# 搜代币
python ai_assistant/main.py search PEPE

# 智能分析
python ai_assistant/main.py analyze PEPE

# 交易计划
python ai_assistant/main.py plan ETH BUY 100 ethereum

# 交易前体检
python ai_assistant/main.py precheck ETH USDC 1 ethereum 0x...

# 大单拆单
python ai_assistant/main.py split ETH USDC 50 ethereum
```

---

## 环境变量

```bash
# OKX API (可选，使用内置测试密钥)
export OKX_API_KEY="your-key"
export OKX_SECRET_KEY="your-secret"
export OKX_PASSPHRASE="your-passphrase"

# Flask
export FLASK_ENV=development
```

---

## 依赖

```
requests>=2.28.0
flask>=2.3.0
flask-cors>=4.0.0
jinja2>=3.1.0
python-dotenv>=1.0.0
```

---

## Changelog

### v3.1 (2026-03-08)
- 修复关键 bug：`track_address` 报错、Holder 分布计算错误、CLI 参数边界崩溃
- 新增交易痛点功能：交易前体检（Pre-trade Check）+ 大单拆单计划（Order Slicing）
- Web 新增“交易体检”面板，CLI 新增 `precheck`/`split` 命令

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
