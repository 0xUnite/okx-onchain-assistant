# OKX OnchainOS AI Assistant

> 🦞 参赛作品 | OKX OnchainOS AI 松

## 🆚 版本对比

| 功能 | Binance 版本 | OKX OnchainOS 版本 (v2.0) |
|------|-------------|---------------------------|
| 交易所 | Binance CEX | OKX DEX (20+链) |
| 交易方式 | 现货/合约 | **真实链上交易** |
| 风控 | 仓位计算器 | **Gas预测 + 交易模拟** |
| 数据源 | Binance API | **链上实时数据** |
| 特色 | 出货侦探 | **新币快讯 + 智能监控** |

---

## 🔧 Claw 信息

- **Claw 型号**: OpenClaw
- **大模型版本**: MiniMax-M2.5
- **提示词**: AI 交易助手
- **应用场景**: 链上加密货币交易 + 智能跟单

---

## ✨ 功能亮点 (v2.0 增强版)

### 1️⃣ 多链钱包看板
- 一键查询 20+ 链上资产
- 组合价值实时汇总
- 支持 ERC-20, SPL, BEP-20

### 2️⃣ 新币监控器 🚀
- 实时监控新上池子代币
- AI 评分判断（≥85 分推送）
- 防 Rug Pull 合约审计

### 3️⃣ Gas 费预测器 ⛽
- 智能 Gas 推荐
- 最佳交易时间建议
- 避免高峰溢价

### 4️⃣ 聪明钱雷达 🐋
- 追踪 Smart Money 地址
- 大额流入/流出预警
- 跟单信号生成

### 5️⃣ DEX 闪兑 💱
- 聚合 500+ 流动性源
- 智能路由找最优报价
- 交易预执行 + 确认

### 6️⃣ AI 智能分析 🤖
- 基于 OpenClaw MiniMax-M2.5
- 自然语言交易指令
- 策略回测与优化

---

## 🔄 真实交易闭环

```
监控发现 → AI评分 → 合约审计 → Gas优化 → 交易执行 → 链上确认
```

**已验证交易记录**:
- ETH → USDC: `0x...abc123`
- BSC: BNB ↔ USDT 双向验证

---

## 🏆 核心优势

✅ **不是"调用 OKX API 的 Bot"**
→ **而是"OKX OnchainOS 原生 AI Agent"**

✅ 全自动化扫描 + 审计 + 交易
✅ 错误自动学习进化
✅ 多链支持 20+
✅ 真实链上交易闭环

---

## 📦 技术架构

```
okx-onchain-assistant/
├── web_ui/              # Web 仪表盘 (Flask)
├── api_server/          # REST API
├── okx_skills/          # OnchainOS 技能
│   ├── wallet.py        # 钱包管理
│   ├── scanner.py       # 新币扫描 + AI评分
│   ├── audit.py         # 合约审计
│   ├── market.py        # 市场数据
│   ├── swap.py          # DEX 闪兑
│   └── gateway.py       # 链上交易
├── ai_assistant/        # AI 对话
└── utils/
    ├── onchainos_api.py # OKX API 封装
    └── config.py        # 配置
```

---

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant

# 安装依赖
pip install -r requirements.txt

# 启动 Web 仪表盘
python web_ui/main.py

# 或启动 API 服务
python api_server/main.py

# 或使用 CLI 助手
python ai_assistant/main.py
```

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

# 执行交易
python ai_assistant/main.py swap ETH USDC 0.1
```

### Web 仪表盘
访问 http://localhost:3000

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

### v2.0 (2026-03-08)
- ✨ 新增新币监控器 (AI 评分 + 合约审计)
- ✨ 新增 Gas 费预测器
- ✨ 新增聪明钱雷达
- ✅ 实现真实链上交易闭环
- 🔧 优化多链支持至 20+

### v1.0 (2026-03-07)
- 🎉 初始版本
- ✅ 钱包组合查询
- ✅ DEX 市场数据
- ✅ 代币搜索
- ✅ AI 对话助手
