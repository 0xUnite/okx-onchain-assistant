# 新手完整教程（从 0 到可用）

这份教程给完全没接触过这个项目的用户，按顺序做即可。

## 1. 准备环境

- 系统：macOS / Linux / Windows（WSL）
- Python：建议 `3.10+`
- 网络：可访问公开 RPC、DexScreener、GoPlus API

检查 Python：

```bash
python3 --version
```

## 2. 下载项目并安装依赖

```bash
git clone https://github.com/0xUnite/okx-onchain-assistant.git
cd okx-onchain-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你在 Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. 第一次运行（不需要私钥）

建议直接跑一键演示：

```bash
python painkiller_demo.py --chain ethereum --wallet 0x742d35Cc6634C0532925a3b844Bc9e7595f
```

你会得到四段输出：
- 交易前体检（Precheck）
- 交易模拟（Simulate）
- 私有交易策略（Private TX Strategy）
- 授权撤销预演（Revoke dry-run）

这一步成功，就说明你的环境是可用的。

## 4. 日常使用（CLI）

### 4.1 进入交互模式

```bash
python ai_assistant/main.py
```

输入 `help` 可查看全部命令。

### 4.2 推荐命令顺序

```bash
# 1) 下单前体检
python ai_assistant/main.py precheck ETH USDC 1 ethereum 0x...

# 2) 交易模拟
python ai_assistant/main.py simulate ETH USDC 1 ethereum 0x...

# 3) 防夹模板
python ai_assistant/main.py private ethereum 5000 0.8

# 4) 授权撤销预演
python ai_assistant/main.py revoke 0x... ethereum
```

## 5. Web 页面使用

```bash
python web_ui/main.py
```

浏览器打开：`http://127.0.0.1:5000`

如果页面打不开，先看 [faq_zh.md](faq_zh.md) 的端口排查。

## 6. 接入 OpenClaw 大模型（可选）

项目默认可运行，但如果你要接入自己的 OpenClaw 服务：

```bash
export OPENCLAW_API_URL="http://127.0.0.1:8080"
export OPENCLAW_MODEL="anthropic/MiniMax-M2.5"
```

然后再执行：

```bash
python ai_assistant/main.py analyze ETH
```

## 7. 真实上链 revoke（可选且高风险）

只有在你确认流程后再做：

```bash
export EVM_PRIVATE_KEY="0x..."
python ai_assistant/main.py revoke 0x... ethereum execute live
```

强烈建议：
- 先做 dry-run
- 先用测试小钱包
- 私钥只保存在本地环境变量

## 8. 验证安装是否完整

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

如果通过，说明核心功能没有明显回归。
