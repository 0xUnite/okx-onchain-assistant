# 预设 Prompts（中文）

这些 Prompt 不是为了显得多，而是为了让用户一上手就知道怎么问，AI 才能像产品而不是命令行脚本。

---

## 1. Daily Briefing
```text
请基于 OKX Onchain Assistant 生成一份 Daily Briefing：
- 关注链：Ethereum, Solana, Base
- 重点 token：ETH, SOL, PEPE, WIF
- 风险偏好：中性
- 输出格式：
  1) 今日结论
  2) 核心指标
  3) 风险提示
  4) 今日行动建议
```

## 2. Deep Dive
```text
请对 {token} 在 {chain} 上做一份 Deep Dive：
- 包括价格、市值、Holder、流动性、合约安全、资金流
- 最后给出 Buy / Wait / Skip 判断
- 风格：专业、简洁、像投研日报
```

## 3. Meme Hunter
```text
请运行 Meme Hunter：
- 链：{chain}
- 最低流动性：{min_liquidity}
- 目标：筛选出最值得盯的 meme 币
- 输出：Top Picks / Watchlist / Avoid List
- 每个项目给出一句理由和一个风险标签
```

## 4. Token Audit
```text
请审计合约 {contract_address}（{chain}）：
- 关注 owner 权限、增发、黑名单、流动性、honeypot 风险
- 输出格式：摘要 / 风险项 / 安全评分 / 是否建议参与
```

## 5. Address Intel
```text
请分析地址 {address}（{chain}）的链上行为：
- 最近 24h 主要操作
- 常用 DEX
- 成交量与频率
- 是否有聪明钱特征
- 是否存在高风险授权
```

## 6. Trade Plan
```text
请为 {token} 在 {chain} 生成交易计划：
- 方向：{BUY_OR_SELL}
- 金额：{amount}
- 结合当前价格、滑点、Gas、资金流
- 输出：入场策略 / 风控 / 止盈止损 / 不执行条件
```

## 7. PM / Demo 模式
```text
你现在是比赛 Demo 模式。
请把输出控制在 60 秒可读完：
- 先给一句结论
- 再给 3 个核心理由
- 再给 2 个风险
- 最后给一个明确动作建议
```

---

## 推荐提示策略

- **想快**：用 Daily Briefing / PM 模式
- **想深**：用 Deep Dive / Address Intel
- **想冲机会**：用 Meme Hunter
- **想避免踩雷**：先跑 Token Audit

一句话：**先问清楚任务，再让 AI 输出结构化结果。**
