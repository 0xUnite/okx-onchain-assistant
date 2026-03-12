"""
OKX OnchainOS AI Assistant - Demo
展示 7 个 Skills 和 4 个工作流的核心输出。
"""
from okx_skills.onchainos_api import OnchainOSClient
from okx_skills.scan_chain import scan_new_tokens, analyze_token, find_smart_money
from okx_skills.audit import ContractAuditor
from okx_skills.analytics import OnchainAnalytics
from okx_skills.security import get_wallet_activity, check_approvals, check_gas
from okx_skills.trading_bot import TradingBot
from okx_skills.reporting import ReportFormatter


def print_section(title: str):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def demo_skill_showcase():
    client = OnchainOSClient()
    auditor = ContractAuditor()
    analytics = OnchainAnalytics()
    bot = TradingBot(max_position_size=2.0)

    print_section("🦞 OKX Onchain Assistant | Skills Showcase")

    # 1) Market Rank / Token Info
    scan_result = scan_new_tokens(chains=["solana"], limit=5)
    top = scan_result["solana"][0]
    deep_report = analyze_token(symbol=top["symbol"], chain="solana")
    print(ReportFormatter.format_token_scan(deep_report))

    # 2) Token Audit
    audit_result = auditor.quick_check("0x742d35Cc6634C0532925a3b844Bc9e7595f", "ethereum")
    print("\n")
    print(ReportFormatter.format_audit_report(audit_result))

    # 3) Trading Signal
    price = client.get_price("PEPE", "ethereum")
    token_info = client.search_token("PEPE", "ethereum")
    flows = client.get_smart_money_flows("ethereum", "PEPE")
    print("\n")
    print(ReportFormatter.format_market_brief("PEPE", "ethereum", price, token_info, flows))

    # 4) Address Info
    address = "0x742d35Cc6634C0532925a3b844Bc9e7595f"
    activity = get_wallet_activity(address, "ethereum")
    print("\n")
    print(ReportFormatter.format_address_report(address, "ethereum", activity))

    # 5) Spot Execution
    print_section("📈 Spot Execution Demo")
    current_price = client.get_price("WETH", "ethereum")["price"]
    stop_loss = current_price * 0.95
    quantity = bot.calculate_position_size(10000, 1.5, current_price, stop_loss)
    open_result = bot.open_position(
        token="WETH",
        chain="ethereum",
        side="LONG",
        entry_price=current_price,
        quantity=quantity,
        stop_loss=stop_loss,
        take_profit=current_price * 1.1,
    )
    print(open_result)
    close_result = bot.close_position("1", current_price * 1.03, "TP")
    print(close_result)
    print(bot.get_pnl_summary())

    # 6) Meme Hunter / On-Chain Intel snippets
    print_section("🧠 Workflow Snippets")
    print("[Daily Briefing] Gas 状态:", check_gas("ethereum"))
    print("[On-Chain Intel] Approval 风险:", check_approvals(address, "ethereum")["risk"])
    print("[Meme Hunter] Smart Money:", find_smart_money("solana"))
    print("[Deep Dive] Pool 分析:", analytics.get_pool_analysis("PEPE", "ethereum"))


def demo_prompts():
    print_section("📝 预设 Prompt 示例")
    prompts = {
        "Daily Briefing": "请给我一份 Daily Briefing：关注链 Ethereum / Solana / Base，重点看 ETH、SOL、PEPE、WIF。",
        "Deep Dive": "请对 PEPE 在 ethereum 上做一份 Deep Dive，包含价格、市值、Holder、流动性、风险和操作建议。",
        "On-Chain Intel": "分析地址 0x742d35Cc6634C0532925a3b844Bc9e7595f 在 ethereum 上最近 24h 的行为和授权风险。",
        "Meme Hunter": "运行 Meme Hunter：链 solana，最低流动性 10000 USD，只保留 AI Score >= 75 的项目。",
        "Trade Plan": "请为 WETH 在 ethereum 生成一份 BUY 交易计划，金额 1000 USDC，输出入场、风控、止盈止损。",
    }
    for name, prompt in prompts.items():
        print(f"\n[{name}]\n{prompt}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "prompts":
        demo_prompts()
    else:
        demo_skill_showcase()
