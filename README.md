# OKX OnchainOS AI Assistant

面向链上交易用户的 AI 助手，核心能力是先做风险体检，再给执行建议。

这个仓库支持两类使用方式：
- 新手：直接跑 CLI/Web，先用 dry-run，不碰私钥
- 进阶：接入 OpenClaw 模型 + 开启 live revoke（真实上链撤销授权）

## 1. 你能解决什么问题

- 下单前不知道风险高不高：`precheck` 给出风险分、阻断项、警告项
- 不确定现在能不能下：`simulate` 输出可执行/阻断 + 最坏成交
- 担心被夹：`private` 输出私有交易模板（优先 private relay）
- 钱包历史无限授权太多：`revoke` 先预演，再选择执行

## 2. 3 分钟跑通（推荐新手）

### 2.1 安装

```bash
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 一键演示（不需要私钥）

```bash
python painkiller_demo.py --chain ethereum --wallet 0x742d35Cc6634C0532925a3b844Bc9e7595f
```

你会看到 4 段结果：
- `[1] Precheck`
- `[2] Simulate`
- `[3] Private TX Strategy`
- `[4] Revoke High-Risk Approvals`

## 3. 新手最常用命令（CLI）

```bash
# 启动交互模式
python ai_assistant/main.py

# 单命令模式（推荐新手）
python ai_assistant/main.py precheck ETH USDC 1 ethereum 0x...
python ai_assistant/main.py simulate ETH USDC 1 ethereum 0x...
python ai_assistant/main.py private ethereum 5000 0.8
python ai_assistant/main.py revoke 0x... ethereum
```

### 命令说明

| 命令 | 用途 | 新手建议 |
|---|---|---|
| `precheck` | 下单前体检 | 先看 `decision` 和 `risk_score` |
| `simulate` | 执行前预演 | 看 `status`、`worst_case_receive` |
| `private` | 防夹交易模板 | 保留默认参数即可 |
| `revoke` | 高风险授权清理 | 先 dry-run，再决定 execute |

## 4. Web 页面使用

```bash
python web_ui/main.py
```

浏览器打开：`http://127.0.0.1:5000`

页面里同样有：
- 交易前体检
- 交易模拟
- 私有交易模板
- 授权撤销（dry-run / execute / live）

## 5. 环境变量（按需配置）

### 5.1 可选：接入 OpenClaw 大模型

```bash
export OPENCLAW_API_URL="http://127.0.0.1:8080"
export OPENCLAW_MODEL="anthropic/MiniMax-M2.5"
```

如果不配置，项目也可以运行，会使用本地 fallback 逻辑。

### 5.2 可选：真实上链撤销授权（高风险）

```bash
export EVM_PRIVATE_KEY="0x..."
```

然后才可以执行：

```bash
python ai_assistant/main.py revoke 0x... ethereum execute live
```

安全建议：
- 永远先执行 dry-run：`revoke 0x... ethereum`
- 小额钱包先试，再用于主钱包
- 私钥只放本地环境变量，不要写入代码或提交 Git

## 6. 项目结构（整理后）

```text
okx-onchain-assistant/
├── ai_assistant/               # CLI 入口
├── web_ui/                     # Web 入口
├── okx_skills/                 # 核心能力模块
├── tests/                      # 单元测试
├── painkiller_demo.py          # 一键演示脚本
├── submission_assets/          # 参赛材料（截图/文档）
└── docs/                       # 新手文档与 FAQ
```

## 7. 新手建议工作流

1. 先跑 `precheck` 看风险  
2. 再跑 `simulate` 看最坏成交  
3. 再看 `private` 模板防夹  
4. 最后再考虑 `revoke` 清理授权  

这套流程比直接 swap 更适合小白，能显著减少误操作。

## 8. 深入文档

- [新手完整教程](docs/quickstart_zh.md)
- [常见问题排查](docs/faq_zh.md)
- [参赛材料汇总](submission_assets/docs/competition_submission_cn.md)
- [提示词清单](submission_assets/docs/prompt_templates_cn.md)

## 9. 开发与测试

```bash
python -m unittest discover -s tests -p "test_*.py" -q
python -m compileall -q .
```

## 10. Changelog（最近）

### v3.4 (2026-03-08)
- 新增真实上链撤销授权能力（`revoke ... execute live`）
- 新增一键演示脚本 `painkiller_demo.py`
- Web 支持 live revoke

### v3.3 (2026-03-08)
- 新增私有交易防夹模板（`private`）
- 新增交易模拟（`simulate_trade`）
- 新增授权撤销流（dry-run + execute）
