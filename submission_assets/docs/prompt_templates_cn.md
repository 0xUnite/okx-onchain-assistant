# 提示词清单（可直接用于答辩/报名）

## 1) 市场分析 Prompt 模板
```text
分析 {token} ({chain}) 市场状况：

价格: ${price}
24h涨跌: {change_24h}%
市值: ${market_cap}
Holder数: {holders}

Smart Money 流向:
- 流入: {total_inflow} ETH
- 流出: {total_outflow} ETH

请给出：
1. 短期趋势判断
2. 关键支撑/阻力位
3. 风险提示
4. 操作建议

保持简洁，2-3句话。
```

## 2) 交易计划 Prompt 模板
```text
生成 {side} {amount} {token} 交易计划：

当前价格: ${price}
预期成交: {to_amount} {token}
价格冲击: {price_impact}%
Gas费用: ${estimated_fee}
滑点建议: {slippage}%

请给出：
1. 入场策略
2. 止盈止损建议
3. 风控要点

简洁明了。
```

## 3) 系统提示词（可选增强版）
```text
你是 OKX 链上交易风控助手。优先使用可验证的链上数据，结论需包含风险等级和可执行建议。
若存在安全隐患（如无限授权、低流动性、异常价格冲击），必须先给出阻断或降风险方案，再给交易建议。
回答保持简洁、结构化，优先中文。
```

## 4) 场景化问句示例
- 交易前体检：`precheck ETH USDC 1 ethereum 0x...`
- 交易可执行性模拟：`simulate ETH USDC 1 ethereum 0x...`
- 防夹模板：`private ethereum 5000 0.8`
- 授权清理：`revoke 0x... ethereum`
