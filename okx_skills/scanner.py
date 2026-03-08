"""
新币扫描器 + AI 评分
实时监控新上池子代币，AI 评分判断是否值得买入
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from okx_skills.onchainos_api import OnchainOSClient

@dataclass
class TokenInfo:
    """代币信息"""
    address: str
    symbol: str
    name: str
    chain: str
    liquidity: float
    market_cap: float
    holders: int
    age_minutes: int  # 上线时间（分钟）
    tx_count: int     # 交易次数
    buy_sell_ratio: float  # 买入/卖出比

class NewTokenScanner:
    """新币扫描器"""
    
    def __init__(self, client: OnchainOSClient = None):
        self.client = client or OnchainOSClient()
        self.min_score = 85  # 最低推送分数
        self.scanned_tokens = set()
    
    def scan_chain(self, chain: str = "ethereum") -> List[TokenInfo]:
        """扫描链上最新代币"""
        # 模拟新币数据（实际需要调用 DEX API）
        sample_tokens = [
            {
                "address": "0x1234567890abcdef",
                "symbol": "PEPE",
                "name": "Pepe",
                "chain": chain,
                "liquidity": 50000,
                "market_cap": 1000000,
                "holders": 1000,
                "age_minutes": 30,
                "tx_count": 500,
                "buy_sell_ratio": 2.5
            },
            {
                "address": "0xabcdef1234567890",
                "symbol": "WIF",
                "name": "dogwifhat",
                "chain": chain,
                "liquidity": 100000,
                "market_cap": 5000000,
                "holders": 5000,
                "age_minutes": 60,
                "tx_count": 2000,
                "buy_sell_ratio": 3.2
            }
        ]
        
        tokens = []
        for t in sample_tokens:
            if t["address"] not in self.scanned_tokens:
                tokens.append(TokenInfo(**t))
                self.scanned_tokens.add(t["address"])
        
        return tokens
    
    def ai_score(self, token: TokenInfo) -> int:
        """AI 评分系统 (0-100)"""
        score = 50  # 基础分
        
        # 流动性评分 (0-15)
        if token.liquidity > 100000:
            score += 15
        elif token.liquidity > 50000:
            score += 10
        elif token.liquidity > 10000:
            score += 5
        
        # 市值评分 (0-10)
        if token.market_cap > 10000000:
            score += 10
        elif token.market_cap > 1000000:
            score += 7
        elif token.market_cap > 100000:
            score += 4
        
        # Holder 评分 (0-10)
        if token.holders > 5000:
            score += 10
        elif token.holders > 1000:
            score += 7
        elif token.holders > 100:
            score += 4
        
        # 活跃度评分 (0-10)
        if token.tx_count > 5000:
            score += 10
        elif token.tx_count > 1000:
            score += 7
        elif token.tx_count > 100:
            score += 4
        
        # 买/卖比评分 (0-10)
        if token.buy_sell_ratio > 3:
            score += 10
        elif token.buy_sell_ratio > 2:
            score += 7
        elif token.buy_sell_ratio > 1.5:
            score += 4
        
        # 新币加成 (0-5)
        if token.age_minutes < 30:
            score += 5
        elif token.age_minutes < 60:
            score += 3
        
        return min(100, score)
    
    def analyze_token(self, token: TokenInfo) -> Dict:
        """深度分析代币"""
        score = self.ai_score(token)
        
        signals = []
        risks = []
        
        # 信号
        if score >= 85:
            signals.append("🔥 高分代币，值得关注")
        if token.buy_sell_ratio > 2:
            signals.append("📈 买入压力大于卖出")
        if token.tx_count > 1000:
            signals.append("🔥 高活跃度")
        if token.liquidity > 50000:
            signals.append("💧 流动性充足")
        
        # 风险
        if token.age_minutes < 10:
            risks.append("⚠️ 新上池子，风险较高")
        if token.holders < 50:
            risks.append("⚠️ Holder 太少，可能归零")
        if token.buy_sell_ratio < 0.5:
            risks.append("⚠️ 卖出压力大于买入")
        
        return {
            "token": token.symbol,
            "chain": token.chain,
            "address": token.address,
            "score": score,
            "signals": signals,
            "risks": risks,
            "recommendation": "BUY" if score >= 85 else "WAIT" if score >= 70 else "SKIP",
            "timestamp": datetime.now().isoformat()
        }
    
    def scan_and_notify(self, chains: List[str] = None) -> List[Dict]:
        """扫描并返回高分数代币"""
        chains = chains or ["ethereum", "bsc", "solana"]
        
        results = []
        for chain in chains:
            tokens = self.scan_chain(chain)
            for token in tokens:
                analysis = self.analyze_token(token)
                if analysis["score"] >= self.min_score:
                    results.append(analysis)
        
        return results


class GasPredictor:
    """Gas 费预测器"""
    
    # 历史数据统计
    GAS_HISTORY = [
        {"hour": 8, "gas_eth": 15, "gas_bsc": 3, "gas_base": 0.5},
        {"hour": 12, "gas_eth": 25, "gas_bsc": 5, "gas_base": 1.0},
        {"hour": 18, "gas_eth": 30, "gas_bsc": 6, "gas_base": 1.5},
        {"hour": 22, "gas_eth": 20, "gas_bsc": 4, "gas_base": 0.8},
    ]
    
    def predict(self, chain: str = "ethereum") -> Dict:
        """预测当前 Gas 费用"""
        import random
        
        # 简化预测（实际需要 ML 模型）
        base_gas = {
            "ethereum": 20,
            "bsc": 5,
            "solana": 0.000025,
            "base": 0.001,
            "arbitrum": 0.1,
            "polygon": 50
        }
        
        current_hour = datetime.now().hour
        
        # 简单波动
        multiplier = 1 + random.uniform(-0.3, 0.3)
        predicted_gas = base_gas.get(chain, 20) * multiplier
        
        return {
            "chain": chain,
            "gas_price": round(predicted_gas, 4),
            "unit": "Gwei" if chain != "solana" else "SOL",
            "recommendation": "BUY" if predicted_gas < base_gas.get(chain, 20) * 0.7 else "WAIT",
            "best_time_hours": [8, 9, 10] if chain == "ethereum" else [],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_optimal_time(self, chain: str = "ethereum") -> Dict:
        """获取最佳交易时间"""
        prediction = self.predict(chain)
        
        if prediction["recommendation"] == "BUY":
            return {
                "status": "good",
                "message": f"当前 {chain} Gas 费用较低，适合交易",
                "current_gas": prediction["gas_price"],
                "unit": prediction["unit"]
            }
        else:
            return {
                "status": "wait",
                "message": f"当前 Gas 费用较高，建议等待",
                "current_gas": prediction["gas_price"],
                "unit": prediction["unit"],
                "suggested_wait_hours": 2
            }


class SmartMoneyRadar:
    """聪明钱雷达"""
    
    # 已知聪明钱地址（模拟）
    WHALE_ADDRESSES = {
        "ethereum": [
            "0x1234...abcd",
            "0x5678...efgh",
            "0xabcd...1234"
        ],
        "bsc": [
            "0xdef0...5678"
        ]
    }
    
    def __init__(self, client: OnchainOSClient = None):
        self.client = client or OnchainOSClient()
    
    def get_whale_flows(self, chain: str = "ethereum", token: str = None) -> Dict:
        """获取大户资金流向"""
        # 模拟数据
        flows = [
            {
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f...",
                "direction": "IN",
                "amount": 100,
                "token": "WETH",
                "usd_value": 300000,
                "tx_hash": "0xabc123..."
            },
            {
                "address": "0x8ba1f109551bD432803012645Hc136E7aF...",
                "direction": "OUT",
                "amount": 50000,
                "token": "USDC",
                "usd_value": 50000,
                "tx_hash": "0xdef456..."
            }
        ]
        
        total_in = sum(f["usd_value"] for f in flows if f["direction"] == "IN")
        total_out = sum(f["usd_value"] for f in flows if f["direction"] == "OUT")
        
        return {
            "chain": chain,
            "token": token,
            "flows": flows,
            "total_inflow_usd": total_in,
            "total_outflow_usd": total_out,
            "net_flow": total_in - total_out,
            "signal": "BUY" if total_in > total_out * 2 else "NEUTRAL",
            "timestamp": datetime.now().isoformat()
        }
    
    def follow_signal(self, chain: str, token: str) -> Dict:
        """跟单信号"""
        flows = self.get_whale_flows(chain, token)
        
        if flows["signal"] == "BUY":
            # 模拟生成跟单交易
            return {
                "action": "FOLLOW_BUY",
                "reason": f"检测到大户净买入 ${flows['net_flow']:,.0f}",
                "amount": 0.01,  # 建议金额
                "token": token,
                "chain": chain,
                "confidence": min(95, 50 + flows["net_flow"] / 10000),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "action": "WAIT",
            "reason": "无明确跟单信号",
            "timestamp": datetime.now().isoformat()
        }


# ===== 便捷函数 =====

def scan_new_tokens(chains: List[str] = None) -> List[Dict]:
    """扫描新币"""
    scanner = NewTokenScanner()
    return scanner.scan_and_notify(chains)

def analyze_token(token_address: str, chain: str = "ethereum") -> Dict:
    """分析代币"""
    scanner = NewTokenScanner()
    # 模拟获取代币信息
    token = TokenInfo(
        address=token_address,
        symbol="UNKNOWN",
        name="Unknown",
        chain=chain,
        liquidity=50000,
        market_cap=1000000,
        holders=1000,
        age_minutes=30,
        tx_count=500,
        buy_sell_ratio=2.0
    )
    return scanner.analyze_token(token)

def predict_gas(chain: str = "ethereum") -> Dict:
    """预测 Gas"""
    predictor = GasPredictor()
    return predictor.predict(chain)

def get_whale_flows(chain: str = "ethereum", token: str = None) -> Dict:
    """获取大户流向"""
    radar = SmartMoneyRadar()
    return radar.get_whale_flows(chain, token)


if __name__ == "__main__":
    # 测试
    print("=== 新币扫描 ===")
    scanner = NewTokenScanner()
    tokens = scanner.scan_chain("ethereum")
    for token in tokens:
        analysis = scanner.analyze_token(token)
        print(f"{token.symbol}: Score {analysis['score']} - {analysis['recommendation']}")
    
    print("\n=== Gas 预测 ===")
    predictor = GasPredictor()
    print(predictor.predict("ethereum"))
    
    print("\n=== 聪明钱雷达 ===")
    radar = SmartMoneyRadar()
    print(radar.get_whale_flows("ethereum", "WETH"))
