"""
合约审计模块
防 Rug Pull，自动审计代币合约安全性
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AuditResult:
    """审计结果"""
    address: str
    chain: str
    score: int  # 0-100
    risks: List[str]
    checks: Dict[str, bool]
    recommendation: str

class ContractAuditor:
    """合约审计器"""
    
    def __init__(self):
        self.min_score = 70  # 最低安全分数
    
    def audit(self, contract_address: str, chain: str = "ethereum") -> AuditResult:
        """审计合约安全性"""
        
        # 模拟审计检查项
        checks = {
            # 流动性相关
            "has_liquidity_lock": True,  # 是否锁流动性
            "liquidity_burned": True,    # 流动性是否烧毁
            "owner_can_mint": False,      # 所有者可以增发
            "owner_can_blacklist": False, # 所有者可以黑名单
            
            # 代码相关
            "has_pause_function": False, # 暂停功能
            "has_tax_function": True,     # 税收功能
            "hidden_owner": False,         # 隐藏所有者
            "honeypot": False,             # 蜜罐代币
            
            # 权限相关
            "mintable": False,             # 可增发
            "burnable": True,              # 可燃烧
            "proxy": False,                # 代理合约
        }
        
        # 计算分数
        score = 100
        
        risks = []
        
        # 扣分项
        if not checks["has_liquidity_lock"]:
            score -= 15
            risks.append("⚠️ 流动性未锁定")
        
        if not checks["liquidity_burned"]:
            score -= 10
            risks.append("⚠️ 流动性未烧毁")
        
        if checks["owner_can_mint"]:
            score -= 30
            risks.append("🚨 所有者可以增发代币（高风险）")
        
        if checks["owner_can_blacklist"]:
            score -= 20
            risks.append("🚨 所有者可以冻结用户资产")
        
        if checks["has_pause_function"]:
            score -= 10
            risks.append("⚠️ 合约可以暂停转账")
        
        if checks["has_tax_function"]:
            score -= 5
            risks.append("⚠️ 存在转账税")
        
        if checks["hidden_owner"]:
            score -= 50
            risks.append("🚨 检测到隐藏所有者（极高风险）")
        
        if checks["honeypot"]:
            score -= 100
            risks.append("🚨 蜜罐代币，无法卖出")
        
        if checks["mintable"]:
            score -= 25
            risks.append("🚨 代币可以无限增发")
        
        score = max(0, min(100, score))
        
        # 建议
        if score >= 90:
            recommendation = "✅ 安全，可以买入"
        elif score >= 70:
            recommendation = "⚠️ 中等风险，小额试试"
        elif score >= 50:
            recommendation = "❌ 高风险，不建议买入"
        else:
            recommendation = "🚨 极度危险，立即远离"
        
        return AuditResult(
            address=contract_address,
            chain=chain,
            score=score,
            risks=risks,
            checks=checks,
            recommendation=recommendation
        )
    
    def quick_check(self, contract_address: str, chain: str = "ethereum") -> Dict:
        """快速检查"""
        result = self.audit(contract_address, chain)
        
        return {
            "address": result.address,
            "chain": result.chain,
            "score": result.score,
            "is_safe": result.score >= self.min_score,
            "recommendation": result.recommendation,
            "top_risks": result.risks[:3],
            "timestamp": datetime.now().isoformat()
        }
    
    def batch_audit(self, addresses: List[str], chain: str = "ethereum") -> List[Dict]:
        """批量审计"""
        results = []
        for addr in addresses:
            result = self.quick_check(addr, chain)
            results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results


def audit_contract(contract_address: str, chain: str = "ethereum") -> Dict:
    """便捷函数：审计合约"""
    auditor = ContractAuditor()
    return auditor.quick_check(contract_address, chain)


if __name__ == "__main__":
    # 测试
    auditor = ContractAuditor()
    
    # 模拟几个代币地址
    test_addresses = [
        "0x742d35Cc6634C0532925a3b844Bc9e7595f",
        "0x1234567890abcdef1234567890abcdef",
        "0xabcdefabcdefabcdefabcdefabcdefabcd"
    ]
    
    print("=== 合约审计 ===")
    results = auditor.batch_audit(test_addresses, "ethereum")
    
    for r in results:
        print(f"\n{r['address'][:20]}...")
        print(f"  分数: {r['score']}/100")
        print(f"  安全: {'✅' if r['is_safe'] else '❌'}")
        print(f"  建议: {r['recommendation']}")
        if r['top_risks']:
            print(f"  风险: {', '.join(r['top_risks'][:2])}")
