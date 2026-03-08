# 常见问题（FAQ）

## 1. `ModuleNotFoundError` / 依赖报错

先确认你激活了虚拟环境并安装依赖：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. `python: command not found` 或 Python 版本过低

- 使用 `python3` 代替 `python`
- 检查版本：`python3 --version`
- 建议 `3.10+`

## 3. Web 页面打不开（`127.0.0.1:5000`）

可能是端口被占用，先看占用进程：

```bash
lsof -i :5000
```

然后结束占用进程，或在代码里改端口后重启。

## 4. 模型请求失败（OpenClaw 不通）

先检查环境变量：

```bash
echo $OPENCLAW_API_URL
echo $OPENCLAW_MODEL
```

再确认 OpenClaw 服务是否已启动。  
即使模型不可用，系统也会回退到本地 fallback 文本。

## 5. `revoke ... execute live` 失败

优先检查：
- 是否设置了 `EVM_PRIVATE_KEY`
- 钱包地址/链是否匹配
- RPC 网络是否可访问
- 账户是否有足够 gas

建议流程：
1. 先 `revoke ...`（dry-run）
2. 再 `revoke ... execute`（模拟执行）
3. 最后才 `revoke ... execute live`

## 6. 输出结果怎么看

- `precheck`  
看 `decision` 和 `risk_score`，有 `blockers` 先不要下单

- `simulate`  
看 `status` 和 `worst_case_receive`，判断最坏成交是否可接受

- `private`  
看 `mode/providers/template`，用于构建防夹下单参数

- `revoke`  
先看候选列表，再决定是否执行

## 7. 怎么确认代码没被我弄坏

```bash
python -m unittest discover -s tests -p "test_*.py" -q
python -m compileall -q .
```

测试通过再继续改功能。
