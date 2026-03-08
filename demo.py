"""
OKX OnchainOS AI 松 - 演示脚本
展示完整工作流
"""
from okx_skills.onchainos_api import OnchainOSClient
from okx_skills.scanner import NewTokenScanner, GasPredictor, SmartMoneyRadar
from okx_skills.audit import ContractAuditor
from okx_skills.analytics import OnchainAnalytics
from okx_skills.trading_bot import TradingBot

def demo_full_workflow():
    """完整工作流演示"""
    print("=" * 60)
    print("🦞 OKX OnchainOS AI Agent - 完整工作流演示")
    print("=" * 60)
    
    client = OnchainOSClient()
    scanner = NewTokenScanner(client)
    gas_predictor = GasPredictor()
    smart_money = SmartMoneyRadar(client)
    auditor = ContractAuditor()
    analytics = OnchainAnalytics()
    bot = TradingBot()
    
    # Step 1: 发现新币
    print("\n📍 Step 1: 发现新币")
    print("-" * 40)
    tokens = scanner.scan_chain("ethereum")
    for token in tokens[:3]:
        analysis = scanner.analyze_token(token)
        print(f"  {token.symbol}: Score {analysis['score']} - {analysis['recommendation']}")
    
    # Step 2: 合约审计
    print("\n📍 Step 2: 合约审计")
    print("-" * 40)
    audit_result = auditor.quick_check("0x742d35Cc6634C0532925a3b844Bc9e7595f", "ethereum")
    print(f"  地址: {audit_result['address'][:20]}...")
    print(f"  安全分数: {audit_result['score']}/100")
    print(f"  建议: {audit_result['recommendation']}")
    if audit_result['top_risks']:
        for risk in audit_result['top_risks']:
            print(f"  {risk}")
    
    # Step 3: Holder 分析
    print("\n📍 Step 3: Holder 分析")
    print("-" * 40)
    holder_data = analytics.get_holder_analysis("PEPE", "ethereum")
    print(f"  代币: {holder_data['token']}")
    print(f"  Holder数: {holder_data['total_holders']}")
    print(f"  Top10集中度: {holder_data['top10_concentration']}%")
    print(f"  风险等级: {holder_data['risk_level']}")
    
    # Step 4: Gas 预测
    print("\n📍 Step 4: Gas 预测")
    print("-" * 40)
    gas = gas_predictor.predict("ethereum")
    print(f"  链: {gas['chain']}")
    print(f"  Gas价格: {gas['gas_price']} {gas['unit']}")
    print(f"  建议: {gas['recommendation']}")
    
    # Step 5: 聪明钱追踪
    print("\n📍 Step 5: 聪明钱追踪")
    print("-" * 40)
    flows = smart_money.get_whale_flows("ethereum", "WETH")
    print(f"  总流入: ${flows['total_inflow_usd']:,.0f}")
    print(f"  总流出: ${flows['total_outflow_usd']:,.0f}")
    print(f"  信号: {flows['signal']}")
    
    # Step 6: 开仓交易
    print("\n📍 Step 6: 开仓交易")
    print("-" * 40)
    price_data = client.get_price("WETH", "ethereum")
    current_price = price_data["price"]
    
    # 计算仓位
    account_balance = 10000  # 假设 10000 U
    risk_pct = 2  # 2% 风险
    stop_loss = current_price * 0.95  # 5% 止损
    
    position_size = bot.calculate_position_size(account_balance, risk_pct, current_price, stop_loss)
    print(f"  当前价格: ${current_price}")
    print(f"  计算仓位: {position_size:.4f} ETH")
    print(f"  止损: ${stop_loss}")
    
    # 执行开仓
    open_result = bot.open_position(
        token="WETH",
        chain="ethereum", 
        side="LONG",
        entry_price=current_price,
        quantity=position_size,
        stop_loss=stop_loss,
        take_profit=current_price * 1.1  # 10% 止盈
    )
    print(f"  开仓结果: {open_result['message']}")
    print(f"  交易Hash: {open_result['tx_hash'][:20]}...")
    
    # Step 7: 检查仓位
    print("\n📍 Step 7: 仓位管理")
    print("-" * 40)
    positions = bot.get_open_positions()
    for p in positions:
        print(f"  仓位 #{p['id']}: {p['side']} {p['quantity']} {p['token']} @ ${p['entry_price']}")
        print(f"    状态: {p['status']}")
    
    # Step 8: 盈亏统计
    print("\n📍 Step 8: 盈亏统计")
    print("-" * 40)
    # 模拟平仓（价格变动）
    close_result = bot.close_position(positions[0]["id"], current_price * 1.02, "TP")
    print(f"  平仓原因: {close_result['reason']}")
    print(f"  盈亏: ${close_result['pnl']:.2f} ({close_result['pnl_pct']:.2f}%)")
    
    summary = bot.get_pnl_summary()
    print(f"  总交易: {summary['total_trades']}")
    print(f"  胜率: {summary['win_rate']}%")
    print(f"  总盈亏: ${summary['total_pnl']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ 完整工作流演示完成!")
    print("=" * 60)


def demo_prompts():
    """提示词示例"""
    print("\n" + "=" * 60)
    print("📝 常用提示词示例")
    print("=" * 60)
    
    prompts = {
        "查余额": "查询 0x742d35Cc6634C0532925a3b844Bc9e7595f 在以太坊上的资产",
        "搜代币": "搜索 PEPE 代币的市值和Holder数量",
        "审计合约": "审计 0x742d35Cc6634C0532925a3b844Bc9e7595f 合约安全性",
        "Gas预测": "现在以太坊 Gas 贵吗？什么时候交易最划算？",
        "查大户": "追踪以太坊上 WETH 的大户资金流向",
        "Holder分析": "分析 PEPE 代币的持币地址分布",
        "池子分析": "查看 PEPE 在 Uniswap 的流动性",
        "兑换": "把 0.1 ETH 兑换成 USDC",
        "跨链": "把 100 USDC 从以太坊跨到 Solana",
        "开仓": "做多 ETH，数量 0.1，止损 2800",
        "平仓": "平掉仓位 #1",
        "复盘": "查看今天的交易统计",
    }
    
    for name, prompt in prompts.items():
        print(f"\n【{name}】")
        print(f"  {prompt}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "prompts":
        demo_prompts()
    else:
        demo_full_workflow()
