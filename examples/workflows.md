# Workflow Examples

下面这 4 个工作流直接参考 Binance Skills 的组织方式，但内容完全贴合本项目当前已有能力。

---

## 1. Daily Briefing
**目标**：每天 3 分钟完成市场扫描，快速生成今天该盯的方向。

### 输入
- 关注链：Ethereum / Solana / Base / BSC
- 关注 token：ETH, SOL, BTC, PEPE, WIF
- 风险偏好：保守 / 中性 / 激进

### 执行步骤
1. 读取重点代币价格、涨跌幅、成交量
2. 读取 Smart Money 流向
3. 扫描新币机会池
4. 检查 Gas 环境
5. 输出一页简报

### 预期输出
- 今日重点观察标的
- 风险提醒
- 值得执行 / 不值得执行的时间窗口

### 示例 Prompt
```text
请给我一份 Daily Briefing：
- 链：Ethereum, Solana, Base
- 重点标的：ETH, SOL, PEPE, WIF
- 风险偏好：中性
- 输出格式：先结论，再表格，再行动建议
```

---

## 2. Deep Dive
**目标**：对单个 token 做完整的研究型拆解。

### 输入
- token symbol 或合约地址
- chain
- 研究目标：短线交易 / 中线观察 / 风险排查

### 执行步骤
1. 读取 Token Info（价格 / 市值 / Holder / 流动性）
2. 执行 Token Audit
3. 做 Holder / Pool / Smart Money 分析
4. 生成结构化分析报告
5. 给出明确结论：Buy / Wait / Skip

### 示例 Prompt
```text
做一份 Deep Dive：
- token: PEPE
- chain: ethereum
- 目标：判断适不适合短线参与
- 输出：摘要 / 核心指标 / 风险 / 操作建议
```

---

## 3. On-Chain Intel
**目标**：围绕地址、资金流和授权风险做链上情报分析。

### 输入
- 钱包地址
- 关注链
- 是否需要授权风险检查

### 执行步骤
1. 读取地址近期行为
2. 分析常用 DEX、成交量、交易频率
3. 检查 approvals / 风险等级
4. 结合 Smart Money 和 token 关联行为做判断
5. 输出地址画像报告

### 示例 Prompt
```text
给我做一份 On-Chain Intel：
- 地址：0x742d35Cc6634C0532925a3b844Bc9e7595f
- 链：ethereum
- 重点：最近 24h 活动、授权风险、是否像聪明钱
```

---

## 4. Meme Hunter
**目标**：快速捕捉 meme 币机会，同时把垃圾项目挡在门外。

### 输入
- 目标链：Solana / Base / BSC
- 最低流动性门槛
- 是否开启审计过滤

### 执行步骤
1. 扫描新币列表
2. 按 AI Score 排序
3. 检查聪明钱信号
4. 过滤高风险合约
5. 输出 Top Picks + Watchlist + Avoid List

### 示例 Prompt
```text
运行 Meme Hunter：
- 链：solana
- 最低流动性：10000 USD
- 只保留 AI Score >= 75 的项目
- 输出：Top 5 候选、每个项目一句话理由、风险等级
```

---

## 推荐展示方式

比赛 Demo 时，最适合演示的是：

1. **Daily Briefing**：体现产品感
2. **Deep Dive**：体现分析深度
3. **Meme Hunter**：体现链上速度感和“机会发现”能力

这三板斧够用了，别把评委淹死在功能堆里。
