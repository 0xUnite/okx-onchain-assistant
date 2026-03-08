"""
Token 授权管理 + Gas 预警 + 钱包监控
链上交易者痛点解决方案
"""
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import time
import random

@dataclass
class Approval:
    """授权信息"""
    token: str
    spender: str  # 授权给谁 (DEX, 合约)
    amount: float
    is_infinite: bool
    chain: str
    tx_hash: str

class TokenApprovalManager:
    """Token 授权管理器"""
    
    def __init__(self):
        self.watched_addresses = {}
    
    def get_approvals(self, address: str, chain: str = "ethereum") -> List[Approval]:
        """查询地址的所有授权"""
        # 模拟授权数据
        approvals = [
            Approval(
                token="USDC",
                spender="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Uniswap V3
                amount=10000,
                is_infinite=False,
                chain=chain,
                tx_hash="0xabc123..."
            ),
            Approval(
                token="USDT",
                spender="0xE592427A0AEce92De3Edee1F18C0157C7C81f0d",  # Uniswap V3
                amount=float('inf'),
                is_infinite=True,
                chain=chain,
                tx_hash="0xdef456..."
            ),
            Approval(
                token="PEPE",
                spender="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Sushiswap
                amount=float('inf'),
                is_infinite=True,
                chain=chain,
                tx_hash="0xghi789..."
            ),
        ]
        
        return approvals
    
    def get_risk_score(self, approvals: List[Approval]) -> Dict:
        """计算授权风险分数"""
        risk_points = 0
        risks = []
        
        for approval in approvals:
            if approval.is_infinite:
                risk_points += 30
                risks.append(f"⚠️ {approval.token} 无限授权给 {approval.spender[:10]}...")
            
            if approval.amount > 1000000:
                risk_points += 10
                risks.append(f"⚠️ {approval.token} 大额授权: ${approval.amount:,.0f}")
        
        risk_level = "HIGH" if risk_points > 50 else "MEDIUM" if risk_points > 20 else "LOW"
        
        return {
            "total_approvals": len(approvals),
            "infinite_approvals": len([a for a in approvals if a.is_infinite]),
            "risk_points": risk_points,
            "risk_level": risk_level,
            "risks": risks,
            "recommendation": "建议撤销不必要的无限授权" if risk_points > 20 else "风险可控",
            "timestamp": datetime.now().isoformat()
        }
    
    def revoke_approval(self, token: str, spender: str, chain: str = "ethereum") -> Dict:
        """撤销授权（模拟）"""
        return {
            "status": "success",
            "token": token,
            "spender": spender,
            "chain": chain,
            "tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
            "message": f"✅ 已撤销 {token} 对 {spender[:10]}... 的授权",
            "timestamp": datetime.now().isoformat()
        }


class GasAlert:
    """Gas 预警系统"""
    
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            "ethereum": {"low": 15, "high": 50, "normal": 30},
            "bsc": {"low": 3, "high": 10, "normal": 5},
            "base": {"low": 0.5, "high": 2, "normal": 1},
        }
    
    def check_gas(self, chain: str = "ethereum") -> Dict:
        """检查当前 Gas"""
        base_gas = {
            "ethereum": 20,
            "bsc": 5,
            "base": 0.8,
            "solana": 0.00001,
            "arbitrum": 0.1,
            "polygon": 40,
        }
        
        current = base_gas.get(chain, 20)
        threshold = self.thresholds.get(chain, {"low": 20, "high": 50})
        
        status = "LOW" if current < threshold["low"] else "HIGH" if current > threshold["high"] else "NORMAL"
        
        return {
            "chain": chain,
            "current_gas": current,
            "unit": "Gwei" if chain != "solana" else "SOL",
            "status": status,
            "threshold": threshold,
            "recommendation": "✅ Gas 低，适合交易" if status == "LOW" else "⚠️ Gas 高，建议等待" if status == "HIGH" else "⏸️ Gas 适中",
            "timestamp": datetime.now().isoformat()
        }
    
    def set_alert(self, chain: str, condition: str, value: float, callback: str = None) -> Dict:
        """设置 Gas 预警"""
        alert = {
            "id": len(self.alerts) + 1,
            "chain": chain,
            "condition": condition,  # "below" or "above"
            "value": value,
            "callback": callback,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        
        return {
            "status": "success",
            "alert_id": alert["id"],
            "message": f"✅ 已设置 {chain} Gas {condition} {value} 时提醒",
            "timestamp": datetime.now().isoformat()
        }
    
    def check_alerts(self) -> List[Dict]:
        """检查预警"""
        triggered = []
        
        for alert in self.alerts:
            if not alert["active"]:
                continue
            
            gas = self.check_gas(alert["chain"])
            
            if alert["condition"] == "below" and gas["current_gas"] < alert["value"]:
                triggered.append(alert)
            elif alert["condition"] == "above" and gas["current_gas"] > alert["value"]:
                triggered.append(alert)
        
        return triggered


class WalletWatcher:
    """钱包监控"""
    
    def __init__(self):
        self.watched_wallets = {}
    
    def watch(self, address: str, name: str = None) -> Dict:
        """添加监控钱包"""
        self.watched_wallets[address.lower()] = {
            "address": address,
            "name": name or address[:10] + "...",
            "added_at": datetime.now().isoformat(),
            "alert_enabled": True
        }
        
        return {
            "status": "success",
            "address": address,
            "name": name,
            "message": f"✅ 已开始监控 {name or address[:10]}...",
            "timestamp": datetime.now().isoformat()
        }
    
    def unwatch(self, address: str) -> Dict:
        """取消监控"""
        addr = address.lower()
        if addr in self.watched_wallets:
            del self.watched_wallets[addr]
            return {"status": "success", "message": f"✅ 已取消监控 {address[:10]}..."}
        
        return {"status": "error", "message": "地址未监控"}
    
    def get_activity(self, address: str, chain: str = "ethereum", limit: int = 10) -> Dict:
        """获取钱包活动"""
        # 模拟交易记录
        activities = []
        for i in range(limit):
            activities.append({
                "hash": f"0x{i:064x}"[:66],
                "type": random.choice(["swap", "transfer", "approve", "nft"]),
                "token_in": random.choice(["ETH", "USDC", "USDT", "PEPE"]),
                "token_out": random.choice(["USDC", "USDT", "WETH", None]),
                "amount_in": round(random.uniform(0.01, 100), 4),
                "amount_out": round(random.uniform(10, 10000), 2) if random.random() > 0.3 else None,
                "dex": random.choice(["Uniswap", "Sushiswap", "Curve", None]),
                "timestamp": datetime.now().timestamp() - i * 3600,
                "gas_used": random.randint(21000, 300000),
                "gas_fee": round(random.uniform(0.001, 0.1), 4)
            })
        
        total_volume = sum(a.get("amount_out", 0) for a in activities if a.get("amount_out"))
        
        return {
            "address": address,
            "chain": chain,
            "activities": activities,
            "total_24h_volume": round(total_volume, 2),
            "tx_count": len(activities),
            "most_used_dex": max(set(a["dex"] for a in activities if a["dex"]), default="N/A"),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_alert_summary(self) -> Dict:
        """获取监控摘要"""
        return {
            "total_watched": len(self.watched_wallets),
            "wallets": [
                {"address": w["address"], "name": w["name"]}
                for w in self.watched_wallets.values()
            ],
            "timestamp": datetime.now().isoformat()
        }


# ===== 便捷函数 =====

def check_approvals(address: str, chain: str = "ethereum") -> Dict:
    """检查授权"""
    manager = TokenApprovalManager()
    approvals = manager.get_approvals(address, chain)
    risk = manager.get_risk_score(approvals)
    
    return {
        "approvals": [
            {
                "token": a.token,
                "spender": a.spender[:20] + "...",
                "amount": "无限" if a.is_infinite else a.amount,
                "chain": a.chain
            }
            for a in approvals
        ],
        "risk": risk
    }

def check_gas(chain: str = "ethereum") -> Dict:
    """检查 Gas"""
    gas_alert = GasAlert()
    return gas_alert.check_gas(chain)

def watch_wallet(address: str, name: str = None) -> Dict:
    """监控钱包"""
    watcher = WalletWatcher()
    return watcher.watch(address, name)

def get_wallet_activity(address: str, chain: str = "ethereum") -> Dict:
    """获取钱包活动"""
    watcher = WalletWatcher()
    return watcher.get_activity(address, chain)


if __name__ == "__main__":
    # 测试
    print("=== Token 授权检查 ===")
    print(check_approvals("0x742d35Cc6634C0532925a3b844Bc9e7595f"))
    
    print("\n=== Gas 检查 ===")
    print(check_gas("ethereum"))
    
    print("\n=== 钱包监控 ===")
    print(watch_wallet("0x742d35Cc6634C0532925a3b844Bc9e7595f", "主钱包"))
    print(get_wallet_activity("0x742d35Cc6634C0532925a3b844Bc9e7595f"))
