"""
OKX OnchainOS AI Assistant
使用 OpenClaw AI 进行智能对话
"""
import os
import json
import sys
from okx_skills.onchainos_api import (
    get_portfolio, get_price, search_token, 
    get_swap_quote, execute_swap, get_smart_money_flows,
    OnchainOSClient
)
from okx_skills.scan_chain import (
    scan_new_tokens, scan_with_conditions, analyze_token, find_smart_money
)
from okx_skills.reporting import ReportFormatter

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
    """结构化市场分析"""
    client = OnchainOSClient()
    price_data = client.get_price(token, chain)
    token_data = client.search_token(token, chain)
    flows = client.get_smart_money_flows(chain, token)
    return ReportFormatter.format_market_brief(token, chain, price_data, token_data, flows)

def generate_trade_plan(token: str, side: str, amount: float, chain: str = "ethereum") -> str:
    """生成结构化交易计划"""
    client = OnchainOSClient()
    normalized_side = side.upper()
    quote = client.get_swap_quote("USDC", token, amount, chain) if normalized_side == "BUY" else client.get_swap_quote(token, "USDC", amount, chain)
    price_data = client.get_price(token, chain)
    gas = client.estimate_gas(chain)
    return ReportFormatter.format_trade_plan(token, normalized_side, chain, price_data, quote, gas)

def handle_command(command: str) -> str:
    """处理用户命令"""
    command = command.lower().strip()
    
    # 钱包查询
    if command.startswith("portfolio ") or command.startswith("钱包 "):
        address = command.split()[-1]
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
        parts = command.split()
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
        query = command.split()[1]
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
        parts = command.replace("swap", "").replace("兑换", "").split()
        if len(parts) >= 3:
            from_token = parts[0].upper()
            to_token = parts[1].upper()
            amount = float(parts[2])
            
            quote = get_swap_quote(from_token, to_token, amount)
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
    elif command.startswith("market ") or command.startswith("市场 ") or command.startswith("analyze "):
        parts = command.split()
        token = parts[1].upper() if len(parts) > 1 else "ETH"
        chain = parts[-1] if len(parts) > 2 else "ethereum"
        return analyze_market(token, chain)

    # 交易计划
    elif command.startswith("plan ") or command.startswith("计划 "):
        parts = command.split()
        if len(parts) < 4:
            return "用法: plan <代币> <BUY/SELL> <金额> [链]"
        token = parts[1].upper()
        side = parts[2].upper()
        amount = float(parts[3])
        chain = parts[4].lower() if len(parts) > 4 else "ethereum"
        return generate_trade_plan(token, side, amount, chain)
    
    # ===== 扫链功能 =====
    # 扫描新币: scan [链] [数量]
    elif command.startswith("scan ") or command.startswith("扫 "):
        parts = command.split()
        
        # 解析参数
        chains = ["solana"]
        limit = 10
        
        for i, part in enumerate(parts[1:]):
            if part.isdigit():
                limit = int(part)
            elif part.lower() in ["solana", "ethereum", "bsc", "base"]:
                chains = [part.lower()]
        
        result = scan_new_tokens(chains=chains, limit=limit)
        
        output = [f"🔍 扫链结果 ({', '.join(chains).upper()})", ""]
        
        for chain, tokens in result.items():
            output.append(f"📌 {chain.upper()}")
            for t in tokens[:8]:
                emoji = "🟢" if t["price_change_24h"] > 0 else "🔴"
                output.append(
                    f"  {emoji} {t['symbol']:10} ${t['price']:.6f} "
                    f"{t['price_change_24h']:+6.1f}% | LC: ${t['liquidity']:>8,.0f}"
                )
            output.append("")
        
        return "\n".join(output)
    
    # 条件扫描: filter [最小流动性] [链]
    elif command.startswith("filter ") or command.startswith("条件 "):
        parts = command.split()
        
        min_liq = 1000
        chains = ["solana", "ethereum", "bsc"]
        
        for part in parts[1:]:
            if part.isdigit():
                min_liq = int(part)
            elif part.lower() in ["solana", "ethereum", "bsc", "base"]:
                chains = [part.lower()]
        
        result = scan_with_conditions(min_liquidity=min_liq, chains=chains)
        
        output = [f"🔍 条件扫描 (流动性>${min_liq:,})", ""]
        for t in result[:10]:
            score = t["score"]
            emoji = "🔥" if score >= 80 else "⚠️" if score >= 70 else "💤"
            output.append(
                f"  {emoji} {t['symbol']:10} Score: {score:3} | "
                f"MC: ${t['market_cap']:>10,.0f}"
            )
        
        return "\n".join(output)
    
    # 代币分析: deep [代币符号] [链]
    elif command.startswith("deep ") or command.startswith("深度 "):
        parts = command.split()
        
        symbol = parts[1].upper() if len(parts) > 1 else None
        chain = parts[-1].lower() if len(parts) > 2 and parts[-1].lower() in ["solana", "ethereum", "bsc"] else "solana"
        
        if not symbol:
            return "请指定代币符号，如: deep PEPE"
        
        result = analyze_token(symbol=symbol, chain=chain)
        
        if "error" in result:
            return f"错误: {result['error']}"
        
        t = result["token"]
        output = [
            f"📊 代币分析: {t['symbol']} ({t['name']})",
            f"Chain: {t['chain']} | DEX: {t['dex']}",
            "",
            f"💰 价格: ${t['price']:.8f}",
            f"📈 24h: {t['price_change_24h']:+.1f}%",
            f"💧 流动性: ${t['liquidity']:,.0f}",
            f"📊 市值: ${t['market_cap']:,.0f}",
            f"⏰ 生命周期: {t['lifecycle']}",
            "",
            f"🎯 AI评分: {result['score']}/100",
            f"💡 建议: {result['recommendation']}",
        ]
        
        if result["signals"]:
            output.append("")
            output.append("✅ 信号:")
            for s in result["signals"]:
                output.append(f"  {s}")
        
        if result["risks"]:
            output.append("")
            output.append("⚠️ 风险:")
            for r in result["risks"]:
                output.append(f"  {r}")
        
        return "\n".join(output)
    
    # Smart Money: whales [链]
    elif command.startswith("whales") or command.startswith("聪明钱"):
        parts = command.split()
        chain = parts[-1].lower() if len(parts) > 1 and parts[-1].lower() in ["solana", "ethereum", "bsc"] else "solana"
        
        result = find_smart_money(chain)
        
        output = [f"🐋 Smart Money 追踪 ({chain.upper()})", ""]
        
        if result["smart_money_tokens"]:
            for t in result["smart_money_tokens"][:8]:
                output.append(
                    f"  🚀 {t['symbol']:10} {t['price_change_24h']:+6.1f}% | "
                    f"Vol: ${t['volume_24h']:,.0f}"
                )
        else:
            output.append("  暂无数据")
        
        return "\n".join(output)
    
    # 帮助
    elif command in ["help", "帮助", "?"]:
        return """
🤖 OKX OnchainOS AI Assistant

核心 Skills:
- Market Rank: scan / filter
- Token Info: price / search / deep
- Token Audit: audit（可在 demo 中展示）
- Trading Signal: market / smart / plan
- Spot Execution: buy / 平仓（示例代码）
- Address Info: portfolio / whales
- Meme Hunter: scan + filter + deep 组合使用

常用命令:
- portfolio <地址>
- price <代币> [链]
- search <代币>
- market <代币> [链]
- plan <代币> <BUY/SELL> <金额> [链]
- scan [链] [数量]
- filter <流动性> [链]
- deep <代币> [链]
- whales [链]

示例:
  market PEPE ethereum
  plan WETH BUY 1000 ethereum
  scan solana 10
  deep WIF solana
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
