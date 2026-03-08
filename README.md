# OKX OnchainOS AI Assistant

> 🦞 参赛作品 | OKX OnchainOS AI 松

## 🆚 版本对比

| 功能 | Binance 版本 | OKX OnchainOS 版本 (v2.1) |
|------|-------------|---------------------------|
| 交易所 | Binance CEX | OKX DEX (20+链) |
| 交易方式 | 现货/合约 | **真实链上交易** |
| 风控 | 仓位计算器 | **Gas预测 + 交易模拟** |
| 数据源 | Binance API | **链上实时数据** |
| 特色 | 出货侦探 | **链上全栈分析** |

---

## 🔧 Claw 信息

- **Claw 型号**: OpenClaw
- **大模型版本**: MiniMax-M2.5
- **提示词**: AI 交易助手
- **应用场景**: 链上加密货币交易 + 智能跟单

---

## ✨ 功能亮点 (v2.2 完整版)

### 交易核心
- **新币监控器** 🚀 - AI 评分 ≥85 推送
- **合约审计** 🔍 - 防 Rug Pull
- **Gas 预测器** ⛽ - 最佳交易时间
- **DEX 闪兑** 💱 - 500+ 流动性源
- **交易机器人** 🤖 - 自动开平仓

### 链上分析
- **Holder 分析** 📊 - 持币分布
- **池子分析** 🏊 - DEX 深度
- **代币热度** 🔥 - 社交情绪
- **聪明钱雷达** 🐋 - 跟单信号

### 高级功能
- **套利扫描** 💰 - 跨 DEX 价差
- **新池子监控** 🎯 - 实时发现
- **闪电贷检测** ⚡ - 反套利预警
- **跨链桥** 🌉 - 多链报价

### 风控安全
- **授权管理** 🔐 - 一键撤销
- **Gas 预警** 📢 - 自动提醒
- **钱包监控** 👁️ - 实时追踪
- **地址追踪** 🔎 - 历史活动

---

## 🔄 完整交易闭环

```
监控发现 → AI评分 → 合约审计 → Holder分析 → Gas优化 → 开仓 → 自动风控 → 平仓
```

---

## 🏆 核心优势

✅ **不是"调用 OKX API 的 Bot"**
→ **而是"OKX OnchainOS 原生 AI Agent"**

✅ 链上数据全覆盖（从发现到平仓）
✅ 自动化交易 + 风控
✅ 多链支持 20+
✅ 真实链上交易闭环

---

## 📦 技术架构

```
okx-onchain-assistant/
├── web_ui/              # Web 仪表盘 (Flask)
├── api_server/         # REST API
├── okx_skills/         # OnchainOS 技能
│   ├── onchainos_api.py   # API 封装
│   ├── scanner.py         # 新币扫描 + AI评分
│   ├── audit.py           # 合约审计
│   ├── analytics.py       # Holder/池子/热度分析
│   ├── trading_bot.py     # 交易机器人
│   ├── market.py          # 市场数据
│   ├── swap.py           # DEX 闪兑
│   └── gateway.py        # 链上交易
├── ai_assistant/      # AI 对话
└── utils/
    └── config.py       # 配置
```

---

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant

# 安装依赖
pip install -r requirements.txt

# 运行演示
python demo.py

# 查看提示词示例
python demo.py prompts

# 启动 Web 仪表盘
python web_ui/main.py

# 或使用 CLI 助手
python ai_assistant/main.py
```

---

## 📝 常用提示词示例

| 场景 | 提示词 |
|------|--------|
| 查余额 | "查询 0x742d... 在以太坊上的资产" |
| 搜代币 | "搜索 PEPE 代币的市值和 Holder 数量" |
| 审计合约 | "审计 0x742d... 合约安全性" |
| Gas 预测 | "现在以太坊 Gas 贵吗？什么时候交易最划算？" |
| 查大户 | "追踪以太坊上 WETH 的大户资金流向" |
| Holder 分析 | "分析 PEPE 代币的持币地址分布" |
| 池子分析 | "查看 PEPE 在 Uniswap 的流动性" |
| 兑换 | "把 0.1 ETH 兑换成 USDC" |
| 跨链 | "把 100 USDC 从以太坊跨到 Solana" |
| 开仓 | "做多 ETH，数量 0.1，止损 2800" |
| 平仓 | "平掉仓位 #1" |
| 复盘 | "查看今天的交易统计" |

---

## 💻 使用示例

### CLI 命令
```bash
# 查询钱包
python ai_assistant/main.py portfolio 0xYourAddress

# 查询价格
python ai_assistant/main.py price ETH

# 新币扫描
python ai_assistant/main.py scan

# 合约审计
python ai_assistant/main.py audit 0x...

# Holder分析
python ai_assistant/main.py holders PEPE

# 开仓
python ai_assistant/main.py buy ETH 0.1
```

---

## 🔐 安全提示

- ⚠️ 测试网验证后再用真钱
- ⚠️ 保护好你的 API Key 和私钥
- ⚠️ 严格仓位控制（建议 2U 测试）
- ⚠️ 本项目仅作研究用途，不构成投资建议

---

## 📅 参赛信息

- **赛事**: OKX OnchainOS AI 松
- **奖项**: 一等奖 3,000 USDT + Mac Mini M5
- **提交**: https://forms.gle/htzQDizcE3rNCp5G9

---

## 🔗 链接

- **GitHub**: https://github.com/0xUnite/okx-onchain-assistant
- **OKX OnchainOS**: https://docs.onchainos.com
- **OKX Developer**: https://web3.okx.com/onchain-os/dev-portal

---

## 📝 Changelog

### v2.2 (2026-03-08)
- ✨ 新增套利扫描器（跨 DEX 价差检测）
- ✨ 新增新池子监控（实时发现 + 分析）
- ✨ 新增闪电贷检测（反套利预警）
- ✨ 新增 Token 授权管理（一键撤销）
- ✨ 新增 Gas 预警系统
- ✨ 新增钱包监控（实时追踪）

### v2.1 (2026-03-08)
- ✨ Holder 分析（持币分布、集中度）
- ✨ 池子分析（DEX 深度、滑点）
- ✨ 代币热度指标
- ✨ 跨链桥报价
- ✨ 地址追踪
- ✨ 交易机器人（自动开平仓、止盈止损）

### v2.0 (2026-03-08)
- ✨ 新增新币监控器 (AI 评分 + 合约审计)
- ✨ 新增 Gas 费预测器
- ✨ 新增聪明钱雷达
- ✅ 实现真实链上交易闭环

### v1.0 (2026-03-07)
- 🎉 初始版本
- ✅ 钱包组合查询
- ✅ DEX 市场数据
- ✅ 代币搜索
- ✅ AI 对话助手
