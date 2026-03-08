"""
OKX OnchainOS Web Dashboard
"""
import os
import sys

from flask import Flask, render_template_string, jsonify, request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from okx_skills.onchainos_api import (
    OnchainOSClient, get_portfolio, get_price, search_token,
    get_swap_quote, execute_swap, get_smart_money_flows
)
from okx_skills.trade_guard import (
    pre_trade_check,
    plan_order_slices,
    route_insight,
    build_private_tx_strategy,
    simulate_trade,
    revoke_high_risk_approvals,
)

app = Flask(__name__)
client = OnchainOSClient()

HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OKX OnchainOS AI 助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .logo { font-size: 24px; font-weight: bold; color: #00d4aa; }
        
        /* Cards */
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h3 { color: #00d4aa; margin-bottom: 16px; font-size: 16px; }
        
        /* Forms */
        input, select, button {
            width: 100%;
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 14px;
        }
        button {
            background: linear-gradient(135deg, #00d4aa, #00a88a);
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { opacity: 0.9; }
        
        /* Results */
        .result {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        
        /* Price Display */
        .price-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .price-item:last-child { border-bottom: none; }
        .price-up { color: #00ff88; }
        .price-down { color: #ff4444; }
        
        /* Tabs */
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            cursor: pointer;
        }
        .tab.active { background: #00d4aa; }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🔷 OKX OnchainOS AI 助手</div>
            <div>基于 OpenClaw AI</div>
        </header>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('portfolio', this)">钱包组合</div>
            <div class="tab" onclick="switchTab('market', this)">市场数据</div>
            <div class="tab" onclick="switchTab('swap', this)">DEX 闪兑</div>
            <div class="tab" onclick="switchTab('guard', this)">交易体检</div>
            <div class="tab" onclick="switchTab('smart', this)">Smart Money</div>
            <div class="tab" onclick="switchTab('ai', this)">AI 助手</div>
        </div>
        
        <!-- Portfolio -->
        <div id="portfolio" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>💰 查询钱包组合</h3>
                    <input type="text" id="walletAddress" placeholder="输入钱包地址 (0x...)">
                    <button onclick="queryPortfolio()">查询</button>
                    <div class="result" id="portfolioResult">输入地址查询多链资产组合</div>
                </div>
            </div>
        </div>

        <!-- Trade Guard -->
        <div id="guard" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🛡️ 交易前体检</h3>
                    <input type="text" id="guardFromToken" placeholder="输入代币 (ETH)" value="ETH">
                    <input type="text" id="guardToToken" placeholder="目标代币 (USDC)" value="USDC">
                    <input type="number" id="guardAmount" placeholder="数量" value="1">
                    <select id="guardChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="solana">Solana</option>
                        <option value="base">Base</option>
                    </select>
                    <input type="text" id="guardWallet" placeholder="钱包地址 (可选)">
                    <button onclick="runPrecheck()">运行体检</button>
                    <div class="result" id="guardResult">检查滑点、Gas、合约安全、地址授权风险</div>
                </div>
                <div class="card">
                    <h3>🧩 大单拆单计划</h3>
                    <input type="text" id="sliceFromToken" placeholder="输入代币 (ETH)" value="ETH">
                    <input type="text" id="sliceToToken" placeholder="目标代币 (USDC)" value="USDC">
                    <input type="number" id="sliceAmount" placeholder="数量" value="50">
                    <select id="sliceChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="solana">Solana</option>
                    </select>
                    <button onclick="runSplitPlan()">生成拆单计划</button>
                    <div class="result" id="sliceResult">降低单笔冲击，减少被夹和吃滑点</div>
                </div>
                <div class="card">
                    <h3>🧭 路由质量快照</h3>
                    <input type="text" id="routeFromToken" placeholder="输入代币 (ETH)" value="ETH">
                    <input type="text" id="routeToToken" placeholder="目标代币 (USDC)" value="USDC">
                    <select id="routeChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="base">Base</option>
                    </select>
                    <button onclick="runRouteInsight()">查询路由</button>
                    <div class="result" id="routeResult">查看可用池子、流动性和24h成交量</div>
                </div>
                <div class="card">
                    <h3>🕶️ 私有交易模板</h3>
                    <select id="privateChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="base">Base</option>
                        <option value="arbitrum">Arbitrum</option>
                        <option value="solana">Solana</option>
                    </select>
                    <input type="number" id="privateTradeUsd" placeholder="交易额USD" value="5000">
                    <input type="number" id="privateSlippage" placeholder="滑点%" value="0.8">
                    <button onclick="runPrivateStrategy()">生成模板</button>
                    <div class="result" id="privateResult">输出 anti-sandwich 参数模板</div>
                </div>
                <div class="card">
                    <h3>🧪 交易模拟</h3>
                    <input type="text" id="simFromToken" placeholder="输入代币 (ETH)" value="ETH">
                    <input type="text" id="simToToken" placeholder="目标代币 (USDC)" value="USDC">
                    <input type="number" id="simAmount" placeholder="数量" value="1">
                    <select id="simChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="base">Base</option>
                    </select>
                    <input type="text" id="simWallet" placeholder="钱包地址 (可选)">
                    <button onclick="runSimulation()">运行模拟</button>
                    <div class="result" id="simResult">输出可执行/阻断与执行模板</div>
                </div>
                <div class="card">
                    <h3>🧹 授权撤销流</h3>
                    <input type="text" id="revokeWallet" placeholder="钱包地址 (0x...)">
                    <select id="revokeChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="base">Base</option>
                    </select>
                    <select id="revokeMode">
                        <option value="dry_run">Dry Run</option>
                        <option value="execute">Execute (Simulated)</option>
                        <option value="execute_live">Execute (Live Onchain)</option>
                    </select>
                    <button onclick="runRevokeFlow()">运行撤销流</button>
                    <div class="result" id="revokeResult">先预演高风险授权，再决定是否执行（Live需 EVM_PRIVATE_KEY）</div>
                </div>
            </div>
        </div>
        
        <!-- Market -->
        <div id="market" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>📊 代币价格</h3>
                    <input type="text" id="priceToken" placeholder="代币符号 (ETH, PEPE, WIF...)" value="ETH">
                    <select id="priceChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="solana">Solana</option>
                        <option value="base">Base</option>
                    </select>
                    <button onclick="queryPrice()">查询价格</button>
                    <div class="result" id="priceResult">查询实时价格和24h变化</div>
                </div>
                <div class="card">
                    <h3>🔍 代币搜索</h3>
                    <input type="text" id="searchToken" placeholder="代币名称或符号">
                    <button onclick="searchToken()">搜索</button>
                    <div class="result" id="searchResult">搜索代币获取市值和Holder信息</div>
                </div>
            </div>
        </div>
        
        <!-- Swap -->
        <div id="swap" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🔄 兑换报价</h3>
                    <input type="text" id="fromToken" placeholder="输入代币 (ETH)" value="ETH">
                    <input type="text" id="toToken" placeholder="目标代币 (USDC)" value="USDC">
                    <input type="number" id="swapAmount" placeholder="数量" value="1">
                    <select id="swapChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="solana">Solana</option>
                    </select>
                    <button onclick="getQuote()">获取报价</button>
                    <div class="result" id="swapResult">获取 DEX 聚合器最佳报价</div>
                </div>
            </div>
        </div>
        
        <!-- Smart Money -->
        <div id="smart" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🐋 Smart Money 追踪</h3>
                    <select id="smartChain">
                        <option value="ethereum">Ethereum</option>
                        <option value="bsc">BSC</option>
                        <option value="solana">Solana</option>
                    </select>
                    <input type="text" id="smartToken" placeholder="代币 (可选)">
                    <button onclick="getSmartMoney()">查询流向</button>
                    <div class="result" id="smartResult">追踪聪明钱地址动向</div>
                </div>
            </div>
        </div>
        
        <!-- AI Chat -->
        <div id="ai" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🤖 AI 智能对话</h3>
                    <input type="text" id="aiQuestion" placeholder="输入问题...">
                    <button onclick="askAI()">提问</button>
                    <div class="result" id="aiResult">基于 OpenClaw AI 的智能问答</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabId, el) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }
        
        async function apiCall(endpoint, data) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            return response.json();
        }
        
        async function queryPortfolio() {
            const address = document.getElementById('walletAddress').value;
            if (!address) return alert('请输入钱包地址');
            document.getElementById('portfolioResult').textContent = '查询中...';
            const result = await apiCall('/api/portfolio', {address});
            document.getElementById('portfolioResult').textContent = JSON.stringify(result, null, 2);
        }
        
        async function queryPrice() {
            const token = document.getElementById('priceToken').value;
            const chain = document.getElementById('priceChain').value;
            document.getElementById('priceResult').textContent = '查询中...';
            const result = await apiCall('/api/price', {token, chain});
            document.getElementById('priceResult').textContent = JSON.stringify(result, null, 2);
        }
        
        async function searchToken() {
            const query = document.getElementById('searchToken').value;
            if (!query) return alert('请输入代币名称');
            document.getElementById('searchResult').textContent = '搜索中...';
            const result = await apiCall('/api/search', {query});
            document.getElementById('searchResult').textContent = JSON.stringify(result, null, 2);
        }
        
        async function getQuote() {
            const from = document.getElementById('fromToken').value;
            const to = document.getElementById('toToken').value;
            const amount = parseFloat(document.getElementById('swapAmount').value);
            const chain = document.getElementById('swapChain').value;
            if (!amount || amount <= 0) return alert('请输入大于0的数量');
            document.getElementById('swapResult').textContent = '获取报价中...';
            const result = await apiCall('/api/quote', {from_token: from, to_token: to, amount, chain});
            document.getElementById('swapResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runPrecheck() {
            const fromToken = document.getElementById('guardFromToken').value;
            const toToken = document.getElementById('guardToToken').value;
            const amount = parseFloat(document.getElementById('guardAmount').value);
            const chain = document.getElementById('guardChain').value;
            const walletAddress = document.getElementById('guardWallet').value;
            if (!amount || amount <= 0) return alert('请输入大于0的数量');
            document.getElementById('guardResult').textContent = '体检中...';
            const result = await apiCall('/api/precheck', {
                from_token: fromToken,
                to_token: toToken,
                amount,
                chain,
                wallet_address: walletAddress || null,
            });
            document.getElementById('guardResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runSplitPlan() {
            const fromToken = document.getElementById('sliceFromToken').value;
            const toToken = document.getElementById('sliceToToken').value;
            const amount = parseFloat(document.getElementById('sliceAmount').value);
            const chain = document.getElementById('sliceChain').value;
            if (!amount || amount <= 0) return alert('请输入大于0的数量');
            document.getElementById('sliceResult').textContent = '生成中...';
            const result = await apiCall('/api/split', {
                from_token: fromToken,
                to_token: toToken,
                amount,
                chain,
            });
            document.getElementById('sliceResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runRouteInsight() {
            const fromToken = document.getElementById('routeFromToken').value;
            const toToken = document.getElementById('routeToToken').value;
            const chain = document.getElementById('routeChain').value;
            document.getElementById('routeResult').textContent = '查询中...';
            const result = await apiCall('/api/route', {
                from_token: fromToken,
                to_token: toToken,
                chain,
            });
            document.getElementById('routeResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runPrivateStrategy() {
            const chain = document.getElementById('privateChain').value;
            const tradeUsd = parseFloat(document.getElementById('privateTradeUsd').value);
            const slippagePct = parseFloat(document.getElementById('privateSlippage').value);
            document.getElementById('privateResult').textContent = '生成中...';
            const result = await apiCall('/api/private-strategy', {
                chain,
                trade_usd: tradeUsd,
                slippage_pct: slippagePct,
            });
            document.getElementById('privateResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runSimulation() {
            const fromToken = document.getElementById('simFromToken').value;
            const toToken = document.getElementById('simToToken').value;
            const amount = parseFloat(document.getElementById('simAmount').value);
            const chain = document.getElementById('simChain').value;
            const walletAddress = document.getElementById('simWallet').value;
            if (!amount || amount <= 0) return alert('请输入大于0的数量');
            document.getElementById('simResult').textContent = '模拟中...';
            const result = await apiCall('/api/simulate', {
                from_token: fromToken,
                to_token: toToken,
                amount,
                chain,
                wallet_address: walletAddress || null,
            });
            document.getElementById('simResult').textContent = JSON.stringify(result, null, 2);
        }

        async function runRevokeFlow() {
            const walletAddress = document.getElementById('revokeWallet').value;
            const chain = document.getElementById('revokeChain').value;
            const mode = document.getElementById('revokeMode').value;
            if (!walletAddress) return alert('请输入钱包地址');
            document.getElementById('revokeResult').textContent = '执行中...';
            const result = await apiCall('/api/revoke', {
                wallet_address: walletAddress,
                chain,
                execute: mode === 'execute' || mode === 'execute_live',
                live: mode === 'execute_live',
            });
            document.getElementById('revokeResult').textContent = JSON.stringify(result, null, 2);
        }
        
        async function getSmartMoney() {
            const chain = document.getElementById('smartChain').value;
            const token = document.getElementById('smartToken').value;
            document.getElementById('smartResult').textContent = '查询中...';
            const result = await apiCall('/api/smart-money', {chain, token: token || null});
            document.getElementById('smartResult').textContent = JSON.stringify(result, null, 2);
        }
        
        async function askAI() {
            const question = document.getElementById('aiQuestion').value;
            if (!question) return alert('请输入问题');
            document.getElementById('aiResult').textContent = 'AI 思考中...';
            const result = await apiCall('/api/ai', {question});
            document.getElementById('aiResult').textContent = result.answer || JSON.stringify(result, null, 2);
        }
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/portfolio', methods=['POST'])
def portfolio():
    data = request.json
    result = get_portfolio(data.get('address', ''))
    return jsonify(result)

@app.route('/api/price', methods=['POST'])
def price():
    data = request.json
    result = get_price(data.get('token', 'ETH'), data.get('chain', 'ethereum'))
    return jsonify(result)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    result = search_token(data.get('query', ''), data.get('chain', 'ethereum'))
    return jsonify(result)

@app.route('/api/quote', methods=['POST'])
def quote():
    data = request.json
    result = get_swap_quote(
        data.get('from_token', 'ETH'),
        data.get('to_token', 'USDC'),
        data.get('amount', 1),
        data.get('chain', 'ethereum')
    )
    return jsonify(result)

@app.route('/api/precheck', methods=['POST'])
def trade_precheck():
    data = request.json or {}
    result = pre_trade_check(
        from_token=data.get('from_token', 'ETH'),
        to_token=data.get('to_token', 'USDC'),
        amount=float(data.get('amount', 1)),
        chain=data.get('chain', 'ethereum'),
        wallet_address=data.get('wallet_address'),
    )
    return jsonify(result)

@app.route('/api/split', methods=['POST'])
def split_plan():
    data = request.json or {}
    result = plan_order_slices(
        from_token=data.get('from_token', 'ETH'),
        to_token=data.get('to_token', 'USDC'),
        amount=float(data.get('amount', 1)),
        chain=data.get('chain', 'ethereum'),
    )
    return jsonify(result)

@app.route('/api/route', methods=['POST'])
def route_quality():
    data = request.json or {}
    result = route_insight(
        from_token=data.get('from_token', 'ETH'),
        to_token=data.get('to_token', 'USDC'),
        chain=data.get('chain', 'ethereum'),
    )
    return jsonify(result)

@app.route('/api/private-strategy', methods=['POST'])
def private_strategy():
    data = request.json or {}
    result = build_private_tx_strategy(
        chain=data.get('chain', 'ethereum'),
        trade_usd=float(data.get('trade_usd', 1000)),
        slippage_pct=float(data.get('slippage_pct', 1.0)),
    )
    return jsonify(result)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json or {}
    result = simulate_trade(
        from_token=data.get('from_token', 'ETH'),
        to_token=data.get('to_token', 'USDC'),
        amount=float(data.get('amount', 1)),
        chain=data.get('chain', 'ethereum'),
        wallet_address=data.get('wallet_address'),
    )
    return jsonify(result)

@app.route('/api/revoke', methods=['POST'])
def revoke():
    data = request.json or {}
    result = revoke_high_risk_approvals(
        wallet_address=data.get('wallet_address', ''),
        chain=data.get('chain', 'ethereum'),
        execute=bool(data.get('execute', False)),
        live=bool(data.get('live', False)),
        private_key=data.get('private_key'),
        max_items=int(data.get('max_items', 8)),
    )
    return jsonify(result)

@app.route('/api/smart-money', methods=['POST'])
def smart_money():
    data = request.json
    result = get_smart_money_flows(data.get('chain', 'ethereum'), data.get('token'))
    return jsonify(result)

@app.route('/api/ai', methods=['POST'])
def ai():
    # 简单的 AI 对接（需要配置实际 AI API）
    from okx_skills.onchainos_api import ask_ai
    data = request.json
    question = data.get('question', '')
    answer = ask_ai(f"你是一个加密货币交易助手。请简洁回答：{question}")
    return jsonify({"answer": answer})

if __name__ == '__main__':
    print("🚀 OKX OnchainOS Dashboard: http://localhost:3000")
    app.run(port=3000, debug=True)
