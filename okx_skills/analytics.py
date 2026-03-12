"""
链上数据分析模块
Holder分析、池子分析、热度指标、跨链桥
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

@dataclass
class HolderInfo:
    """持币者信息"""
    address: str
    balance: float
    percent: float  # 持仓占比
    is_contract: bool
    is_whale: bool  # 是否大户

class OnchainAnalytics:
    """链上分析器"""
    
    def __init__(self):
        self.whale_threshold = 100  # ETH
    
    def get_holder_analysis(self, token: str, chain: str = "ethereum") -> Dict:
        """Holder 分析"""
        # 模拟数据
        holders = [
            HolderInfo("0x742d35Cc6634C0532925a3b844Bc9e7595f", 5000, 45, False, True),
            HolderInfo("0x8ba1f109551bD432803012645Hc136E7aF", 1000, 9, False, True),
            HolderInfo("0x1234567890abcdef1234567890abcdef", 500, 4.5, False, False),
            HolderInfo("0xabcdefabcdefabcdefabcdefabcdefabcd", 300, 2.7, False, False),
            HolderInfo("0x11112222333344445555666677778888", 200, 1.8, True, False),
        ]
        
        # 模拟小holder
        for i in range(95):
            holders.append(HolderInfo(
                f"0x{i:064x}"[:42],
                random.uniform(0.1, 10),
                0,
                False,
                False
            ))
        
        # 计算占比
        total = sum(h.balance for h in holders)
        for h in holders:
            h.percent = (h.balance / total) * 100 if total > 0 else 0
        
        top10_pct = sum(h.percent for h in sorted(holders, key=lambda x: x.balance, reverse=True)[:10])
        
        return {
            "token": token,
            "chain": chain,
            "total_holders": len(holders),
            "top10_concentration": round(top10_pct, 2),
            "whale_count": len([h for h in holders if h.is_whale]),
            "contract_count": len([h for h in holders if h.is_contract]),
            "distribution": {
                "top10": round(top10_pct, 2),
                "top50": round(sum(h.percent for h in sorted(holders, key=lambda x: x.balance, reverse=True)[:50]), 2),
                "rest": round(100 - top10_pct - sum(h.percent for h in sorted(holders, key=lambda x: x.balance, reverse=True)[:50]), 2)
            },
            "top_holders": [
                {
                    "address": h.address[:10] + "...",
                    "balance": round(h.balance, 4),
                    "percent": round(h.percent, 2),
                    "is_whale": h.is_whale
                }
                for h in sorted(holders, key=lambda x: x.balance, reverse=True)[:5]
            ],
            "risk_level": "HIGH" if top10_pct > 50 else "MEDIUM" if top10_pct > 30 else "LOW",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_pool_analysis(self, token: str, chain: str = "ethereum") -> Dict:
        """池子分析"""
        # 模拟 DEX 池子数据
        pools = [
            {
                "dex": "Uniswap V3",
                "pair": f"{token}/WETH",
                "liquidity": 1500000,
                "volume_24h": 500000,
                "apr": 25.5
            },
            {
                "dex": "Sushiswap",
                "pair": f"{token}/USDC",
                "liquidity": 800000,
                "volume_24h": 200000,
                "apr": 18.2
            },
            {
                "dex": "Curve",
                "pair": f"{token}/USDT",
                "liquidity": 500000,
                "volume_24h": 100000,
                "apr": 12.0
            }
        ]
        
        total_liquidity = sum(p["liquidity"] for p in pools)
        total_volume = sum(p["volume_24h"] for p in pools)
        
        return {
            "token": token,
            "chain": chain,
            "pools": pools,
            "total_liquidity": total_liquidity,
            "total_volume_24h": total_volume,
            "avg_slippage": round(total_volume / total_liquidity * 100, 2) if total_liquidity > 0 else 0,
            "recommendation": "SAFE" if total_liquidity > 1000000 else "CAUTION" if total_liquidity > 100000 else "RISKY",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_token_heat(self, token: str, chain: str = "ethereum") -> Dict:
        """代币热度指标"""
        return {
            "token": token,
            "chain": chain,
            "social_score": random.randint(60, 100),
            "trending_rank": random.randint(1, 100),
            "mentions_24h": random.randint(100, 10000),
            "google_trends": random.randint(20, 80),
            "twitter_followers": random.randint(1000, 100000),
            "sentiment": "BULLISH" if random.random() > 0.4 else "BEARISH",
            "momentum": "HIGH" if random.random() > 0.6 else "MEDIUM" if random.random() > 0.3 else "LOW",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_cross_bridge_quote(self, from_chain: str, to_chain: str, token: str, amount: float) -> Dict:
        """跨链桥报价"""
        # 模拟跨链桥
        bridges = [
            {"name": "Stargate", "fee": 0.001, "time": "10-30min", "slippage": 0.5},
            {"name": "LayerZero", "fee": 0.0005, "time": "5-15min", "slippage": 0.3},
            {"name": "Axelar", "fee": 0.002, "time": "15-45min", "slippage": 0.8},
        ]
        
        best = min(bridges, key=lambda x: x["fee"])
        
        return {
            "from_chain": from_chain,
            "to_chain": to_chain,
            "token": token,
            "amount": amount,
            "received_amount": amount * (1 - best["fee"]),
            "bridge": best["name"],
            "fee": best["fee"],
            "estimated_time": best["time"],
            "slippage": best["slippage"],
            "timestamp": datetime.now().isoformat()
        }
    
    def track_address(self, address: str, chain: str = "ethereum") -> Dict:
        """地址追踪"""
        # 模拟交易历史
        txs = []
        for i in range(10):
            txs.append({
                "hash": f"0x{i:064x}"[:66],
                "type": "IN" if i % 2 == 0 else "OUT",
                "token": random.choice(["WETH", "USDC", "USDT", "DAI"]),
                "amount": round(random.uniform(0.1, 100), 4),
                "timestamp": datetime.now().timestamp() - i * 3600,
                "dex": random.choice(["Uniswap", "Sushiswap", "Curve"])
            })
        
        return {
            "address": address,
            "chain": chain,
            "total_txs": len(txs),
            "total_inflow": sum(t["amount"] for t in txs if t["type"] == "IN"),
            "total_outflow": sum(t["amount"] for t in txs if t["type"] == "OUT"),
            "favorite_dex": max((t["dex"] for t in txs), key=lambda dex: sum(1 for tx in txs if tx["dex"] == dex)),
            "recent_transactions": txs[:5],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_nft_portfolio(self, address: str, chain: str = "ethereum") -> Dict:
        """NFT 持仓查询"""
        # 模拟 NFT 数据
        nfts = [
            {
                "collection": "BoredApeYachtClub",
                "token_id": "1234",
                "floor_price": 15.5,
                "last_sale": 18.0
            },
            {
                "collection": "PudgyPenguins",
                "token_id": "5678",
                "floor_price": 3.2,
                "last_sale": 3.5
            }
        ]
        
        total_value = sum(n["floor_price"] for n in nfts)
        
        return {
            "address": address,
            "chain": chain,
            "nfts": nfts,
            "total_value_eth": total_value,
            "total_value_usd": total_value * 3000,  # 假设 ETH = $3000
            "count": len(nfts),
            "timestamp": datetime.now().isoformat()
        }


# ===== 便捷函数 =====

def analyze_holders(token: str, chain: str = "ethereum") -> Dict:
    """Holder分析"""
    analytics = OnchainAnalytics()
    return analytics.get_holder_analysis(token, chain)

def analyze_pool(token: str, chain: str = "ethereum") -> Dict:
    """池子分析"""
    analytics = OnchainAnalytics()
    return analytics.get_pool_analysis(token, chain)

def get_token_heat(token: str, chain: str = "ethereum") -> Dict:
    """热度指标"""
    analytics = OnchainAnalytics()
    return analytics.get_token_heat(token, chain)

def bridge_token(from_chain: str, to_chain: str, token: str, amount: float) -> Dict:
    """跨链桥"""
    analytics = OnchainAnalytics()
    return analytics.get_cross_bridge_quote(from_chain, to_chain, token, amount)

def track_address(address: str, chain: str = "ethereum") -> Dict:
    """地址追踪"""
    analytics = OnchainAnalytics()
    return analytics.track_address(address)


if __name__ == "__main__":
    analytics = OnchainAnalytics()
    
    print("=== Holder 分析 ===")
    print(analytics.get_holder_analysis("PEPE", "ethereum"))
    
    print("\n=== 池子分析 ===")
    print(analytics.get_pool_analysis("PEPE", "ethereum"))
    
    print("\n=== 热度 ===")
    print(analytics.get_token_heat("PEPE", "ethereum"))
    
    print("\n=== 跨链桥 ===")
    print(analytics.get_cross_bridge_quote("ethereum", "solana", "USDC", 1000))
