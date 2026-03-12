# OKX Onchain Assistant Skills Map

参考 Binance 官方 Skills 的拆法，我们把本项目整理成 **7 个独立技能模块 + 4 个工作流**。重点不是把功能堆在一起，而是让用户知道：**什么时候该调用哪个能力**。

---

## 7 个独立 Skills

### 1. Market Rank
**目标**：快速筛出值得看、值得追踪、值得放弃的标的。

**对应能力**
- `okx_skills.scan_chain.scan_new_tokens`
- `okx_skills.scan_chain.scan_with_conditions`
- `okx_skills.scan_chain.analyze_token`

**适用场景**
- 我现在该看哪些新币？
- 哪些代币流动性、市值、活跃度达标？
- 今天哪个链上机会密度最高？

**典型输出**
- 排行榜
- Watchlist
- 候选池 / 黑名单

---

### 2. Token Info
**目标**：给单个代币建立基础画像。

**对应能力**
- `okx_skills.onchainos_api.get_price`
- `okx_skills.onchainos_api.search_token`
- `okx_skills.onchainos_api.get_token_analytics`
- `okx_skills.analytics.get_holder_analysis`
- `okx_skills.analytics.get_pool_analysis`

**适用场景**
- 这个币现在价格多少？
- 市值、Holder、流动性如何？
- 这个 token 是不是只有叙事没有结构？

---

### 3. Token Audit
**目标**：在下单前先做安全筛查，避免把自己送进蜜罐。

**对应能力**
- `okx_skills.audit.ContractAuditor`
- `okx_skills.audit_report`
- `okx_skills.reporting.ReportFormatter.format_audit_report`

**适用场景**
- 这个合约能不能碰？
- 有没有 owner / mint / blacklist / tax 风险？
- 是否适合纳入候选池？

---

### 4. Trading Signal
**目标**：把价格、情绪、资金流和执行成本拼成交易信号。

**对应能力**
- `ai_assistant.main.analyze_market`
- `ai_assistant.main.generate_trade_plan`
- `okx_skills.onchainos_api.get_smart_money_flows`
- `okx_skills.reporting.ReportFormatter.format_trade_plan`

**适用场景**
- 该不该进？
- 进场位置和风险回报是否合理？
- 当前 Gas 和滑点是否值得执行？

---

### 5. Spot Execution
**目标**：执行交易、管理仓位、做复盘。

**对应能力**
- `okx_skills.trading_bot.open_position`
- `okx_skills.trading_bot.close_position`
- `okx_skills.trading_bot.get_open_positions`
- `okx_skills.trading_bot.get_pnl_summary`

**适用场景**
- 开仓 / 平仓
- 止盈止损管理
- 今日交易回顾

---

### 6. Address Info
**目标**：围绕地址建立行为画像，辅助识别聪明钱和风险钱包。

**对应能力**
- `okx_skills.analytics.track_address`
- `okx_skills.security.watch_wallet`
- `okx_skills.security.get_wallet_activity`
- `okx_skills.reporting.ReportFormatter.format_address_report`

**适用场景**
- 这个地址是不是聪明钱？
- 它常用哪些 DEX？
- 最近 24h 在做什么？

---

### 7. Meme Hunter
**目标**：针对 meme 币场景做更激进但更结构化的机会捕捉。

**对应能力**
- `okx_skills.scan_chain.find_smart_money`
- `okx_skills.scan_chain.analyze_token`
- `okx_skills.security.check_gas`
- `okx_skills.audit.audit_contract`

**适用场景**
- Solana / Base / BSC 上有哪些新热点？
- 哪些 meme 有流动性、有活跃度、有资金关注？
- 哪些只是典型的一日游陷阱？

---

## 设计原则

1. **先筛选，再深挖，再执行**
2. **先安全，再收益**
3. **输出必须结构化，方便 AI 继续处理**
4. **每个 Skill 单一职责，不做“万能大杂烩”**

---

## 推荐调用路径

- 想发现机会：`Market Rank -> Meme Hunter -> Token Audit`
- 想研究单币：`Token Info -> Trading Signal -> Spot Execution`
- 想追踪大户：`Address Info -> Trading Signal -> Spot Execution`

这套拆法的好处很直接：**更像产品，不像脚本合集。**
