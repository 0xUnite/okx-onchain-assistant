"""
交易痛点模块

1) 交易前体检：在下单前统一评估滑点/Gas/安全风险
2) 大单拆单：降低单笔冲击和潜在被夹风险
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from okx_skills.analytics import OnchainAnalytics
from okx_skills.audit import ContractAuditor
from okx_skills.onchainos_api import OnchainOSClient
from okx_skills.security import TokenApprovalManager


def _now() -> str:
    return datetime.now().isoformat()


class TradeGuard:
    """交易安全与执行质量守卫。"""

    def __init__(self, client: Optional[OnchainOSClient] = None):
        self.client = client or OnchainOSClient()
        self.auditor = ContractAuditor()
        self.analytics = OnchainAnalytics()
        self.approval_manager = TokenApprovalManager()

    def pre_trade_check(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain: str = "ethereum",
        wallet_address: Optional[str] = None,
        max_slippage_pct: float = 1.5,
        max_gas_fee_usd: float = 20.0,
    ) -> Dict:
        """下单前统一检查，输出 PASS/WARN/BLOCK。"""
        amount = float(amount or 0)
        blockers: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        risk_score = 0

        if amount <= 0:
            return {
                "decision": "BLOCK",
                "risk_score": 100,
                "blockers": ["交易数量必须大于 0"],
                "warnings": [],
                "suggestions": ["调整下单数量后重试"],
                "timestamp": _now(),
            }

        quote = self.client.get_swap_quote(from_token, to_token, amount, chain)
        if quote.get("error"):
            return {
                "decision": "BLOCK",
                "risk_score": 100,
                "blockers": [quote["error"]],
                "warnings": [],
                "suggestions": ["检查交易对和数量是否有效"],
                "timestamp": _now(),
            }

        # 1) 成交质量（滑点/冲击）
        price_impact = float(quote.get("price_impact", 0.0))
        if price_impact > max_slippage_pct * 2:
            blockers.append(f"价格冲击 {price_impact:.2f}% 过高，可能严重滑点")
            risk_score += 40
        elif price_impact > max_slippage_pct:
            warnings.append(f"价格冲击 {price_impact:.2f}% 高于阈值 {max_slippage_pct:.2f}%")
            risk_score += 20
            suggestions.append("建议拆单执行，或等待更深流动性时段")

        # 2) Gas 成本
        gas = self.client.estimate_gas(chain)
        gas_fee = float(gas.get("estimated_fee", 0))
        if gas_fee > max_gas_fee_usd * 2:
            blockers.append(f"预估 Gas ${gas_fee:.2f} 过高")
            risk_score += 25
        elif gas_fee > max_gas_fee_usd:
            warnings.append(f"预估 Gas ${gas_fee:.2f} 偏高")
            risk_score += 12
            suggestions.append("建议等待低 Gas 时段再交易")

        # 3) 合约审计（模拟地址）
        pseudo_address = f"0x{to_token.lower().encode('utf-8').hex():0<40}"[:42]
        audit = self.auditor.quick_check(pseudo_address, chain)
        if audit["score"] < 60:
            blockers.append(f"合约安全分 {audit['score']} 偏低")
            risk_score += 30
        elif audit["score"] < 80:
            warnings.append(f"合约安全分 {audit['score']}，建议小仓位试单")
            risk_score += 15

        # 4) 持仓集中度
        holder = self.analytics.get_holder_analysis(to_token.upper(), chain)
        top10 = float(holder.get("top10_concentration", 0))
        if top10 > 85:
            warnings.append(f"Top10 持仓占比 {top10:.2f}% 偏高，存在控盘风险")
            risk_score += 15
            suggestions.append("设置更紧止损，避免重仓追涨")

        # 5) 授权风险（有钱包地址时）
        approval_risk = None
        if wallet_address:
            approvals = self.approval_manager.get_approvals(wallet_address, chain)
            approval_risk = self.approval_manager.get_risk_score(approvals)
            if approval_risk["risk_level"] == "HIGH":
                warnings.append("钱包存在高风险无限授权")
                risk_score += 10
                suggestions.append("先撤销无限授权再执行交易")

        decision = "PASS"
        if blockers:
            decision = "BLOCK"
        elif warnings or risk_score >= 20:
            decision = "WARN"

        if not suggestions:
            suggestions.append("当前风控可接受，可按计划执行")

        return {
            "decision": decision,
            "risk_score": min(100, int(risk_score)),
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "amount": amount,
            "chain": chain,
            "checks": {
                "quote": quote,
                "gas": gas,
                "audit": audit,
                "holders": {
                    "top10_concentration": top10,
                    "risk_level": holder.get("risk_level"),
                },
                "approval_risk": approval_risk,
            },
            "blockers": blockers,
            "warnings": warnings,
            "suggestions": suggestions,
            "timestamp": _now(),
        }

    def plan_order_slices(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain: str = "ethereum",
        max_single_impact_pct: float = 1.2,
    ) -> Dict:
        """根据当前报价冲击，给出拆单执行计划。"""
        amount = float(amount or 0)
        if amount <= 0:
            return {
                "status": "error",
                "message": "amount 必须大于 0",
                "timestamp": _now(),
            }

        quote = self.client.get_swap_quote(from_token, to_token, amount, chain)
        if quote.get("error"):
            return {"status": "error", "message": quote["error"], "timestamp": _now()}

        impact = float(quote.get("price_impact", 0.0))
        # 基于冲击粗略计算需要拆分数量
        chunks = 1 if impact <= max_single_impact_pct else min(8, max(2, int(impact // max_single_impact_pct) + 1))
        chunk_amount = amount / chunks
        estimated_chunk_impact = round(impact / chunks * 1.15, 4)

        schedule = []
        for i in range(chunks):
            schedule.append(
                {
                    "index": i + 1,
                    "from_amount": round(chunk_amount, 8),
                    "wait_seconds": 0 if i == 0 else 20,
                    "max_slippage_pct": round(max_single_impact_pct, 2),
                    "estimated_price_impact_pct": estimated_chunk_impact,
                }
            )

        return {
            "status": "ok",
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "amount": amount,
            "chain": chain,
            "original_price_impact_pct": round(impact, 4),
            "recommended_slices": chunks,
            "estimated_slice_impact_pct": estimated_chunk_impact,
            "schedule": schedule,
            "timestamp": _now(),
        }


_guard = TradeGuard()


def pre_trade_check(
    from_token: str,
    to_token: str,
    amount: float,
    chain: str = "ethereum",
    wallet_address: Optional[str] = None,
    max_slippage_pct: float = 1.5,
    max_gas_fee_usd: float = 20.0,
) -> Dict:
    return _guard.pre_trade_check(
        from_token=from_token,
        to_token=to_token,
        amount=amount,
        chain=chain,
        wallet_address=wallet_address,
        max_slippage_pct=max_slippage_pct,
        max_gas_fee_usd=max_gas_fee_usd,
    )


def plan_order_slices(
    from_token: str,
    to_token: str,
    amount: float,
    chain: str = "ethereum",
    max_single_impact_pct: float = 1.2,
) -> Dict:
    return _guard.plan_order_slices(
        from_token=from_token,
        to_token=to_token,
        amount=amount,
        chain=chain,
        max_single_impact_pct=max_single_impact_pct,
    )

