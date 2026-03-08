"""
交易痛点模块

1) 交易前体检：滑点/Gas/安全/授权/路由质量
2) 大单拆单：按流动性动态分片，降低冲击和被夹风险
"""
from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Dict, List, Optional

from okx_skills.analytics import OnchainAnalytics
from okx_skills.audit import ContractAuditor
from okx_skills.onchainos_api import OnchainOSClient
from okx_skills.security import TokenApprovalManager


def _now() -> str:
    return datetime.now().isoformat()


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class TradeGuard:
    """交易安全与执行质量守卫。"""

    def __init__(self, client: Optional[OnchainOSClient] = None):
        self.client = client or OnchainOSClient()
        self.auditor = ContractAuditor()
        self.analytics = OnchainAnalytics()
        self.approval_manager = TokenApprovalManager()

    def _compute_sandwich_risk(
        self,
        trade_usd: float,
        best_liquidity_usd: float,
        price_impact_pct: float,
        slippage_pct: float,
    ) -> Dict:
        """估算被夹风险（轻量启发式）。"""
        if best_liquidity_usd <= 0:
            score = min(100, int(35 + price_impact_pct * 10))
        else:
            size_ratio = trade_usd / max(best_liquidity_usd, 1)
            score = int(
                min(
                    100,
                    12
                    + price_impact_pct * 8
                    + max(0.0, slippage_pct - 1) * 6
                    + size_ratio * 500,
                )
            )

        if score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {"score": score, "level": level}

    def route_insight(self, from_token: str, to_token: str, chain: str = "ethereum") -> Dict:
        route = self.client.get_route_snapshot(from_token, to_token, chain)
        routes = route.get("routes", [])
        if not routes:
            return {
                "chain": chain,
                "from_token": from_token.upper(),
                "to_token": to_token.upper(),
                "quality": "UNKNOWN",
                "message": "未找到可用路由池子，建议换交易对或链",
                "routes": [],
                "timestamp": _now(),
            }

        best = routes[0]
        best_liq = _safe_float(best.get("liquidity_usd"))
        quality = "POOR"
        if best_liq > 2_000_000:
            quality = "DEEP"
        elif best_liq > 300_000:
            quality = "OK"

        return {
            "chain": chain,
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "quality": quality,
            "message": f"最佳池子 {best.get('dex')} 流动性 ${best_liq:,.0f}",
            "best_liquidity_usd": best_liq,
            "best_route": best,
            "routes": routes,
            "timestamp": _now(),
        }

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

        from_price = _safe_float(self.client.get_price(from_token, chain).get("price"), 0.0)
        trade_usd = amount * from_price

        route = self.client.get_route_snapshot(from_token, to_token, chain)
        best_liq = _safe_float(route.get("best_liquidity_usd"), 0.0)
        if not route.get("routes"):
            warnings.append("未命中实时路由池，报价精度下降")
            risk_score += 10
        elif best_liq < max(50_000, trade_usd * 20):
            warnings.append(f"最佳池子流动性偏浅 (${best_liq:,.0f})")
            risk_score += 15
            suggestions.append("建议降低单笔规模或换到流动性更深的池子")

        # 1) 成交质量（滑点/冲击）
        price_impact = _safe_float(quote.get("price_impact"), 0.0)
        if price_impact > max_slippage_pct * 2:
            blockers.append(f"价格冲击 {price_impact:.2f}% 过高，可能严重滑点")
            risk_score += 40
        elif price_impact > max_slippage_pct:
            warnings.append(f"价格冲击 {price_impact:.2f}% 高于阈值 {max_slippage_pct:.2f}%")
            risk_score += 20
            suggestions.append("建议拆单执行，或等待更深流动性时段")

        sandwich = self._compute_sandwich_risk(
            trade_usd=trade_usd,
            best_liquidity_usd=best_liq,
            price_impact_pct=price_impact,
            slippage_pct=_safe_float(quote.get("slippage"), max_slippage_pct),
        )
        if sandwich["level"] == "HIGH":
            warnings.append(f"MEV/被夹风险较高 (score={sandwich['score']})")
            risk_score += 18
            suggestions.append("建议提高私有交易保护/降低滑点/加大拆单粒度")
        elif sandwich["level"] == "MEDIUM":
            warnings.append(f"MEV/被夹风险中等 (score={sandwich['score']})")
            risk_score += 8

        # 2) Gas 成本
        gas = self.client.estimate_gas(chain)
        gas_fee = _safe_float(gas.get("estimated_fee"), 0)
        if gas_fee > max_gas_fee_usd * 2:
            blockers.append(f"预估 Gas ${gas_fee:.2f} 过高")
            risk_score += 25
        elif gas_fee > max_gas_fee_usd:
            warnings.append(f"预估 Gas ${gas_fee:.2f} 偏高")
            risk_score += 12
            suggestions.append("建议等待低 Gas 时段再交易")

        # 3) 合约审计（优先实时）
        token_security = self.client.get_token_security(to_token, chain)
        if token_security.get("available"):
            sec_score = int(token_security.get("score", 0))
            sec_flags = token_security.get("risk_flags", [])
            if sec_score < 60:
                blockers.append(f"合约安全分 {sec_score} 偏低")
                risk_score += 30
            elif sec_score < 80:
                warnings.append(f"合约安全分 {sec_score}，建议小仓位试单")
                risk_score += 15
            if sec_flags:
                warnings.extend([f"安全项: {flag}" for flag in sec_flags[:2]])
                risk_score += min(10, len(sec_flags) * 5)
        else:
            # Fallback to local audit logic
            pseudo_address = f"0x{to_token.lower().encode('utf-8').hex():0<40}"[:42]
            fallback_audit = self.auditor.quick_check(pseudo_address, chain)
            token_security = {
                "available": False,
                "source": "fallback/local-audit",
                "score": fallback_audit["score"],
                "risk_flags": fallback_audit.get("top_risks", []),
                "summary": {},
            }
            if fallback_audit["score"] < 60:
                blockers.append(f"合约安全分 {fallback_audit['score']} 偏低")
                risk_score += 30

        # 4) Holder 风险（优先实时 holder_count）
        holder_view = {"top10_concentration": None, "risk_level": "UNKNOWN", "holder_count": None, "source": "none"}
        holder_count = token_security.get("summary", {}).get("holder_count")
        if holder_count:
            holder_count = int(holder_count)
            holder_view = {"top10_concentration": None, "risk_level": "LOW" if holder_count > 5000 else "MEDIUM", "holder_count": holder_count, "source": "goplus/live"}
            if holder_count < 1000:
                warnings.append(f"持币地址较少 ({holder_count})，流动性与控盘风险偏高")
                risk_score += 10
                suggestions.append("避免重仓，优先小仓位试单")
        else:
            holder = self.analytics.get_holder_analysis(to_token.upper(), chain)
            top10 = _safe_float(holder.get("top10_concentration"), 0)
            holder_view = {
                "top10_concentration": top10,
                "risk_level": holder.get("risk_level"),
                "holder_count": holder.get("total_holders"),
                "source": "local/analytics",
            }
            if top10 > 85:
                warnings.append(f"Top10 持仓占比 {top10:.2f}% 偏高，存在控盘风险")
                risk_score += 15
                suggestions.append("设置更紧止损，避免重仓追涨")

        # 5) 授权风险（优先实时）
        approval_risk = None
        if wallet_address:
            approval_risk = self.client.get_wallet_approval_risk(wallet_address, chain)
            if not approval_risk.get("available"):
                approvals = self.approval_manager.get_approvals(wallet_address, chain)
                fallback = self.approval_manager.get_risk_score(approvals)
                approval_risk = {
                    "available": False,
                    "source": "fallback/local",
                    "total_approvals": fallback["total_approvals"],
                    "infinite_approvals": fallback["infinite_approvals"],
                    "risk_points": fallback["risk_points"],
                    "risk_level": fallback["risk_level"],
                    "items": [],
                }

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
                "route": route,
                "gas": gas,
                "token_security": token_security,
                "holders": holder_view,
                "approval_risk": approval_risk,
                "sandwich_risk": sandwich,
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
        """根据报价冲击 + 路由流动性，给出拆单执行计划。"""
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

        from_price = _safe_float(self.client.get_price(from_token, chain).get("price"), 0.0)
        trade_usd = amount * from_price
        route = self.client.get_route_snapshot(from_token, to_token, chain)
        best_liq = _safe_float(route.get("best_liquidity_usd"), 0.0)

        impact = _safe_float(quote.get("price_impact"), 0.0)
        if best_liq > 0 and trade_usd > 0:
            # Inverse from quote impact model: impact ~= trade_usd / liq * 120
            per_slice_usd = best_liq * max_single_impact_pct / 120
            chunks = max(1, ceil(trade_usd / max(per_slice_usd, 1)))
        else:
            chunks = 1 if impact <= max_single_impact_pct else max(2, int(impact // max_single_impact_pct) + 1)

        chunks = min(12, chunks)
        chunk_amount = amount / chunks
        estimated_chunk_impact = round(max(0.05, impact / chunks * 1.1), 4)

        gas = self.client.estimate_gas(chain)
        wait_seconds = 20 if gas.get("recommendation") == "BUY" else 35

        schedule = []
        for i in range(chunks):
            schedule.append(
                {
                    "index": i + 1,
                    "from_amount": round(chunk_amount, 8),
                    "wait_seconds": 0 if i == 0 else wait_seconds,
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
            "trade_usd": round(trade_usd, 2),
            "best_liquidity_usd": round(best_liq, 2),
            "route_source": route.get("source"),
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


def route_insight(from_token: str, to_token: str, chain: str = "ethereum") -> Dict:
    return _guard.route_insight(from_token, to_token, chain)
