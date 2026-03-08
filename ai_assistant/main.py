"""
OKX OnchainOS AI Assistant
使用 OpenClaw AI 进行智能对话
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from okx_skills.onchainos_api import (
    get_portfolio, get_price, search_token, 
    get_swap_quote, execute_swap, get_smart_money_flows,
    OnchainOSClient
)
from okx_skills.trade_guard import pre_trade_check, plan_order_slices, route_insight

# 使用 OpenClaw 内置 AI（通过环境变量）
OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "http://127.0.0.1:8080")

def ask_ai(prompt: str, system_prompt: str = None) -> str:
    """调用 OpenClaw AI API"""
    import requests
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = requests.post(
            f"{OPENCLAW_API_URL}/v1/chat/completions",
            json={
                "model": "anthropic/MiniMax-M2.5",
                "messages": messages,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_market(token: str, chain: str = "ethereum") -> str:
    """AI 市场分析"""
    # 获取数据
    client = OnchainOSClient()
    price_data = client.get_price(token, chain)
    token_data = client.search_token(token, chain)
    flows = client.get_smart_money_flows(chain, token)
    
    # 构建分析提示
    prompt = f"""分析 {token} ({chain}) 市场状况：

价格: ${price_data['price']:.6f}
24h涨跌: {price_data['change_24h']:+.2f}%
市值: ${token_data.get('market_cap', 0):,}
Holder数: {token_data.get('holders', 0):,}

Smart Money 流向:
- 流入: {flows.get('total_inflow', 0)} ETH
- 流出: {flows.get('total_outflow', 0)} ETH

请给出：
1. 短期趋势判断
2. 关键支撑/阻力位
3. 风险提示
4. 操作建议

保持简洁，2-3句话。"""
    
    return ask_ai(prompt)

def generate_trade_plan(token: str, side: str, amount: float, chain: str = "ethereum") -> str:
    """生成交易计划"""
    client = OnchainOSClient()
    price_data = client.get_price(token, chain)
    quote = client.get_swap_quote("USDC", token, amount, chain) if side == "BUY" else client.get_swap_quote(token, "USDC", amount, chain)
    gas = client.estimate_gas(chain)
    
    prompt = f"""生成 {side} {amount} {token} 交易计划：

当前价格: ${price_data['price']:.6f}
预期成交: {quote['to_amount']:.6f} {token}
价格冲击: {quote['price_impact']:.2f}%
Gas费用: ${gas['estimated_fee']:.4f}
滑点建议: {quote['slippage']}%

请给出：
1. 入场策略
2. 止盈止损建议
3. 风控要点

简洁明了。"""
    
    return ask_ai(prompt)

def handle_command(command: str) -> str:
    """处理用户命令"""
    command = command.lower().strip()
    parts = command.split()
    
    # 钱包查询
    if command.startswith("portfolio ") or command.startswith("钱包 "):
        if len(parts) < 2:
            return "请提供钱包地址，例如: portfolio 0x..."
        address = parts[-1]
        portfolio = get_portfolio(address)
        return f"""
💰 钱包组合

地址: {portfolio['address']}
总价值: ${portfolio['total_value_usd']:,.2f}

资产分布:
{chr(10).join([f"- {a['chain']}: {a['symbol']} x {a['amount']} (${a['value_usd']:,.2f})" for a in portfolio['assets']])}

更新时间: {portfolio['timestamp']}
"""
    
    # 价格查询
    elif command.startswith("price ") or command.startswith("价格 "):
        token = parts[1].upper() if len(parts) > 1 else "ETH"
        chain = parts[-1] if len(parts) > 2 else "ethereum"
        
        price = get_price(token, chain)
        return f"""
📊 {token} 价格 ({chain})

价格: ${price['price']:.6f}
24h涨跌: {price['change_24h']:+.2f}%
24h成交量: ${price['volume_24h']:,.0f}

更新时间: {price['timestamp']}
"""
    
    # 代币搜索
    elif command.startswith("search ") or command.startswith("搜索 "):
        if len(parts) < 2:
            return "请提供代币关键字，例如: search PEPE"
        query = parts[1]
        token = search_token(query)
        return f"""
🔍 代币搜索: {query}

符号: {token['symbol']}
名称: {token['name']}
市值: ${token.get('market_cap', 0):,}
Holder: {token.get('holders', 0):,}
价格: ${token['price']:.8f}

更新时间: {token['timestamp']}
"""
    
    # 兑换报价
    elif "swap" in command or "兑换" in command:
        # 格式: swap ETH USDC 1
        swap_parts = command.replace("swap", "").replace("兑换", "").split()
        if len(swap_parts) < 3:
            return "格式错误，示例: swap ETH USDC 1"

        from_token = swap_parts[0].upper()
        to_token = swap_parts[1].upper()
        try:
            amount = float(swap_parts[2])
        except ValueError:
            return "数量格式错误，示例: swap ETH USDC 1"

        quote = get_swap_quote(from_token, to_token, amount)
        if quote.get("error"):
            return f"报价失败: {quote['error']}"

        return f"""
🔄 兑换报价: {from_token} -> {to_token}

输入: {amount} {from_token}
预计成交: {quote['to_amount']:.6f} {to_token}
价格冲击: {quote['price_impact']:.2f}%
Gas费用: ${quote['gas_fee']:.4f}
建议滑点: {quote['slippage']}%

更新时间: {quote['timestamp']}
"""
    
    # Smart Money
    elif "smart" in command or "聪明钱" in command:
        parts = command.replace("smart", "").replace("聪明钱", "").split()
        chain = parts[0] if parts else "ethereum"
        
        flows = get_smart_money_flows(chain)
        return f"""
🐋 Smart Money 流向 ({chain})

总流入: {flows['total_inflow']} ETH
总流出: {flows['total_outflow']} ETH
净流入: {flows['total_inflow'] - flows['total_outflow']} ETH

近期大额交易:
{chr(10).join([f"- {f['direction']}: {f['amount']} {f['token']}" for f in flows['flows'][:5]])}

更新时间: {flows['timestamp']}
"""
    
    # 市场分析
    elif command.startswith("analyze ") or command.startswith("分析 "):
        token = parts[1].upper() if len(parts) > 1 else "ETH"
        chain = parts[-1] if len(parts) > 2 else "ethereum"
        
        return analyze_market(token, chain)

    # 交易计划
    elif command.startswith("plan "):
        # plan ETH buy 100 ethereum
        if len(parts) < 4:
            return "格式错误，示例: plan ETH BUY 100 ethereum"
        token = parts[1].upper()
        side = parts[2].upper()
        if side not in {"BUY", "SELL"}:
            return "side 仅支持 BUY 或 SELL"
        try:
            amount = float(parts[3])
        except ValueError:
            return "金额格式错误，示例: plan ETH BUY 100"
        chain = parts[4] if len(parts) > 4 else "ethereum"
        return generate_trade_plan(token, side, amount, chain)

    # 交易前体检
    elif command.startswith("precheck "):
        # precheck ETH USDC 1 ethereum 0x...
        if len(parts) < 4:
            return "格式错误，示例: precheck ETH USDC 1 ethereum 0x..."
        from_token = parts[1].upper()
        to_token = parts[2].upper()
        try:
            amount = float(parts[3])
        except ValueError:
            return "数量格式错误，示例: precheck ETH USDC 1"
        chain = parts[4] if len(parts) > 4 else "ethereum"
        wallet = parts[5] if len(parts) > 5 else None
        result = pre_trade_check(from_token, to_token, amount, chain=chain, wallet_address=wallet)
        holder_view = result["checks"]["holders"]
        top10 = holder_view.get("top10_concentration")
        holder_line = f"{top10}%" if top10 is not None else f"{holder_view.get('holder_count')} holders"

        return f"""
🛡️ 交易前体检 ({from_token}->{to_token}, {chain})

结论: {result['decision']}
风险分: {result['risk_score']}/100
价格冲击: {result['checks']['quote']['price_impact']}%
Gas 预估: ${result['checks']['gas']['estimated_fee']}
合约分: {result['checks']['token_security']['score']}
持仓观察: {holder_line}
三明治风险: {result['checks']['sandwich_risk']['level']} ({result['checks']['sandwich_risk']['score']})

阻断项:
{chr(10).join(['- ' + b for b in result['blockers']]) if result['blockers'] else '- 无'}

警告项:
{chr(10).join(['- ' + w for w in result['warnings']]) if result['warnings'] else '- 无'}

建议:
{chr(10).join(['- ' + s for s in result['suggestions']])}
"""

    # 大单拆单
    elif command.startswith("split "):
        # split ETH USDC 50 ethereum
        if len(parts) < 4:
            return "格式错误，示例: split ETH USDC 50 ethereum"
        from_token = parts[1].upper()
        to_token = parts[2].upper()
        try:
            amount = float(parts[3])
        except ValueError:
            return "数量格式错误，示例: split ETH USDC 50"
        chain = parts[4] if len(parts) > 4 else "ethereum"
        result = plan_order_slices(from_token, to_token, amount, chain=chain)
        if result.get("status") == "error":
            return f"拆单失败: {result['message']}"

        rows = []
        for s in result["schedule"]:
            rows.append(
                f"- 第{s['index']}笔: {s['from_amount']} {from_token}, 等待{s['wait_seconds']}s, "
                f"预计冲击 {s['estimated_price_impact_pct']}%"
            )

        return f"""
🧩 大单拆单计划 ({from_token}->{to_token}, {chain})

原始冲击: {result['original_price_impact_pct']}%
推荐拆分: {result['recommended_slices']} 笔
单笔预计冲击: {result['estimated_slice_impact_pct']}%

执行计划:
{chr(10).join(rows)}
"""

    # 路由质量
    elif command.startswith("route "):
        # route ETH USDC ethereum
        if len(parts) < 3:
            return "格式错误，示例: route ETH USDC ethereum"
        from_token = parts[1].upper()
        to_token = parts[2].upper()
        chain = parts[3] if len(parts) > 3 else "ethereum"
        result = route_insight(from_token, to_token, chain)
        routes = result.get("routes", [])
        if not routes:
            return f"路由建议: {result['message']}"
        top_lines = []
        for item in routes[:3]:
            top_lines.append(
                f"- {item['dex']} | liq ${item['liquidity_usd']:,.0f} | vol24h ${item['volume_h24_usd']:,.0f}"
            )
        return f"""
🧭 路由质量 ({from_token}->{to_token}, {chain})

质量: {result['quality']}
说明: {result['message']}

Top Routes:
{chr(10).join(top_lines)}
"""
    
    # 帮助
    elif command in ["help", "帮助", "?"]:
        return """
🤖 OKX OnchainOS AI 助手

命令:
- portfolio <地址> - 查询钱包组合
- price <代币> [链] - 查询价格
- search <代币> - 搜索代币
- swap <从> <到> <数量> - 兑换报价
- smart [链] - Smart Money 流向
- analyze <代币> - AI 市场分析
- plan <代币> <买卖> <金额> - 生成交易计划
- precheck <从> <到> <数量> [链] [钱包地址] - 交易前体检
- split <从> <到> <数量> [链] - 大单拆单计划
- route <从> <到> [链] - 查看路由质量/池子深度

示例:
  price ETH
  search PEPE
  swap ETH USDC 1
  analyze PEPE
  precheck ETH USDC 1 ethereum 0xabc...
  split ETH USDC 50 ethereum
  route ETH USDC ethereum
"""
    
    else:
        return ask_ai(command)

def main():
    print("=" * 50)
    print("🤖 OKX OnchainOS AI Assistant")
    print("=" * 50)
    print()
    
    if len(sys.argv) > 1:
        # 命令行模式
        command = " ".join(sys.argv[1:])
        result = handle_command(command)
        print(result)
    else:
        # 交互模式
        print("输入命令或问题（help 查看帮助）:")
        print()
        
        while True:
            try:
                command = input("> ").strip()
                if not command:
                    continue
                if command in ["exit", "quit", "退出"]:
                    break
                    
                result = handle_command(command)
                print(result)
                print()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
