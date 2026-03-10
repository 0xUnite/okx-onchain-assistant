# OKX OnchainOS AI 松参赛素材

## 1. Claw 型号、大模型版本

```text
Claw 型号: OpenClaw
大模型版本: MiniMax-M2.5
```

---

## 2. 项目定位

**OKX OnchainOS AI Assistant** 是一个面向链上交易场景的 AI 助手，不只是提供信息，而是把 **市场感知、AI 决策、自动执行、动态风控** 串成完整闭环。

核心目标：让用户从“手动盯盘 + 手动下单”升级到“AI 发现机会 + AI 判断风险 + 自动完成执行”。

---

## 3. 创新功能亮点

### 🤖 AI 网格策略
- AI 分析波动率、趋势强弱、成交活跃度
- 自动设置最优网格区间、网格层数、间距与资金分配
- 降低传统网格策略依赖人工调参的问题

### 📰 新闻情绪交易
- 实时抓取新闻、社媒、热点事件
- 用 AI 分析市场情绪，识别利多/利空信号
- 将情绪信号直接联动交易执行，实现自动反应

### 🐋 鲸鱼跟单
- 追踪聪明钱地址、大额钱包和链上异动
- 识别高价值买卖行为与资金流向
- 结合 OKX 的交易能力实现一键跟单

### 📊 智能止盈止损
- AI 根据波动率、趋势变化和持仓状态动态调整止盈止损
- 避免固定 TP/SL 在高波动行情中失效
- 提升策略适应性与风险控制能力

---

## 4. 提示词与应用场景

### 核心提示词
```text
你是一个链上加密货币交易助手，擅长：
- AI 网格策略生成与优化
- 新闻情绪分析与交易执行
- 聪明钱/鲸鱼地址追踪与跟单
- 智能止盈止损与动态风控
- 新币发现、合约审计、Holder/池子分析
```

### 典型应用场景
```text
1. 监控多链市场波动，自动生成最优 AI 网格参数
2. 实时抓取新闻与情绪变化，自动执行利多/利空交易
3. 追踪聪明钱地址，发现高价值链上资金动向并跟单
4. 根据实时波动率动态调整止盈止损，避免被短时波动洗出
5. 审计新币合约，防 Rug Pull、蜜罐与黑名单风险
6. 监控 Gas、池子深度与滑点，优化交易时机
```

---

## 5. 示例对话 / 演示文案

### 示例 1：AI 网格策略
```text
用户: 帮我给 ETH 配一套网格策略
助手: 🤖 AI 分析中...
- 当前波动率: 高
- 趋势判断: 震荡偏多
- 推荐区间: 2,850 - 3,180
- 网格数量: 12
- 单格间距: 2.7%
- 建议仓位: 40%

结论: 已为你生成一套适合当前波动环境的 AI 网格策略。
```

### 示例 2：新闻情绪交易
```text
用户: 现在 BTC 有什么交易信号？
助手: 📰 正在抓取新闻与社媒情绪...
- ETF 资金流入相关新闻增多
- 社媒情绪: 强烈看多
- 波动率: 上升

交易建议: 顺势做多，轻仓进场；若情绪反转将自动减仓。
```

### 示例 3：鲸鱼跟单
```text
用户: 最近聪明钱在买什么？
助手: 🐋 监控到 3 个聪明钱地址正在加仓 PEPE
- 地址A: 买入 $120,000
- 地址B: 买入 $85,000
- 地址C: 买入 $64,000

建议: 资金正在集中流入，可开启 OKX 一键跟单。
```

### 示例 4：智能止盈止损
```text
用户: 给我做多 ETH，顺便管好止盈止损
助手: 📊 已开仓并启用智能风控
- 仓位: LONG 0.1 ETH @ $3,000
- 初始止损: $2,880
- 初始止盈: $3,280
- 模式: AI 动态调整

说明: 若波动率扩大，系统会自动放宽止损并上移止盈。
```

---

## 6. 核心代码示例

### AI 网格策略
```python
from okx_skills.ai_brain import backtest_strategy

result = backtest_strategy("AI_GRID", "ETH", 30)
print(result)
```

### 新闻情绪交易
```python
from okx_skills.ai_brain import ai_decide

decision = ai_decide(
    signal={
        "token": "BTC",
        "news_sentiment": "bullish",
        "event": "macro_positive"
    },
    market={
        "volatility": "high",
        "trend": "up",
        "rsi": 61
    }
)
print(decision)
```

### 鲸鱼跟单 / 地址分析
```python
from okx_skills.analytics import analyze_holders

result = analyze_holders("PEPE", "ethereum")
print(result)
```

### 智能止盈止损 + 自动交易
```python
from okx_skills.trading_bot import open_position

result = open_position(
    token="ETH",
    chain="ethereum",
    side="LONG",
    entry_price=3000,
    quantity=0.1,
    stop_loss=2880,
    take_profit=3280
)
print(result)
```

---

## 7. 当前项目目录结构

```text
okx-onchain-assistant/
├── CONTENT.md
├── CONTENT_V2.md
├── README.md
├── ai_assistant/
│   └── main.py
├── demo.py
├── okx_skills/
│   ├── ai_brain.py
│   ├── analytics.py
│   ├── audit.py
│   ├── monitor.py
│   ├── onchainos_api.py
│   ├── scanner.py
│   ├── security.py
│   └── trading_bot.py
├── requirements.txt
└── web_ui/
    └── main.py
```

---

## 8. GitHub 链接

```text
https://github.com/0xUnite/okx-onchain-assistant
```
