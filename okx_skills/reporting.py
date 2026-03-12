"""
统一报告输出模块
让市场分析、审计、地址分析、交易计划输出更专业、更适合比赛展示。
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional


def _fmt_number(value, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if abs(num) >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if abs(num) >= 1_000:
        return f"{num / 1_000:.2f}K"
    if abs(num) >= 1:
        return f"{num:,.{digits}f}"
    return f"{num:.6f}"


def _fmt_money(value, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"${float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_pct(value, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        num = float(value)
        sign = "+" if num > 0 else ""
        return f"{sign}{num:.{digits}f}%"
    except (TypeError, ValueError):
        return str(value)


def _bullet_lines(items: Optional[Iterable[str]], empty: str = "- 无") -> str:
    items = [str(i) for i in (items or []) if str(i).strip()]
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


class ReportFormatter:
    """统一的 Markdown 风格分析报告输出器"""

    @staticmethod
    def build_report(
        title: str,
        summary: str,
        score: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metrics: Optional[Dict[str, str]] = None,
        findings: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        disclaimer: str = "仅供研究与演示，不构成投资建议。",
    ) -> str:
        lines = [f"# {title}", ""]
        lines.append(f"**摘要**：{summary}")
        if score is not None:
            lines.append(f"**评分**：{score}/100")
        if tags:
            lines.append(f"**标签**：{' | '.join(tags)}")

        if metrics:
            lines.extend(["", "## 核心指标"])
            for key, value in metrics.items():
                lines.append(f"- **{key}**：{value}")

        if findings is not None:
            lines.extend(["", "## 关键结论", _bullet_lines(findings)])

        if risks is not None:
            lines.extend(["", "## 风险提示", _bullet_lines(risks)])

        if actions is not None:
            lines.extend(["", "## 建议动作", _bullet_lines(actions)])

        lines.extend([
            "",
            f"_生成时间：{datetime.now().isoformat(timespec='seconds')}_",
            f"_免责声明：{disclaimer}_",
        ])
        return "\n".join(lines)

    @classmethod
    def format_market_brief(cls, token: str, chain: str, price_data: Dict, token_data: Dict, flows: Dict) -> str:
        net_flow = float(flows.get("total_inflow", 0)) - float(flows.get("total_outflow", 0))
        findings = [
            f"{token.upper()} 当前价格 {_fmt_money(price_data.get('price'), 6)}，24h 变动 {_fmt_pct(price_data.get('change_24h'))}。",
            f"市值 {_fmt_money(token_data.get('market_cap'))}，Holder {_fmt_number(token_data.get('holders'), 0)}，说明资产关注度已有基础。",
            f"Smart Money 净流向 {_fmt_number(net_flow, 2)}，可作为短线情绪确认信号。",
        ]
        risks = [
            "若流动性不足或价格冲击偏高，短线信号会明显失真。",
            "单一聪明钱流向不应直接等同于可执行买卖指令。",
        ]
        actions = [
            "结合支撑/阻力与成交量做二次确认。",
            "若是高波动 meme 币，优先小仓位试错。",
            "执行前检查滑点、Gas 与止损位。",
        ]
        return cls.build_report(
            title=f"{token.upper()} 市场简报",
            summary=f"面向 {chain} 的快速市场扫描，适合 Daily Briefing / Deep Dive 的第一屏结论。",
            tags=[chain, "Market", "Brief"],
            metrics={
                "当前价格": _fmt_money(price_data.get("price"), 6),
                "24h 涨跌": _fmt_pct(price_data.get("change_24h")),
                "24h 成交量": _fmt_money(price_data.get("volume_24h")),
                "市值": _fmt_money(token_data.get("market_cap")),
                "Holder": _fmt_number(token_data.get("holders"), 0),
                "Smart Money 流入": _fmt_number(flows.get("total_inflow"), 2),
                "Smart Money 流出": _fmt_number(flows.get("total_outflow"), 2),
            },
            findings=findings,
            risks=risks,
            actions=actions,
        )

    @classmethod
    def format_token_scan(cls, analysis: Dict) -> str:
        token = analysis.get("token", {})
        findings = list(analysis.get("signals") or [])
        risks = list(analysis.get("risks") or [])
        actions = [
            f"当前建议：{analysis.get('recommendation', 'WAIT')}。",
            "若进入观察名单，继续跟踪流动性、成交量和生命周期变化。",
            "若评分低于 70，除非有额外 alpha，不建议强行参与。",
        ]
        return cls.build_report(
            title=f"{token.get('symbol', 'TOKEN')} 深度分析",
            summary=f"针对 {token.get('chain', 'unknown')} 新币机会的结构化报告。",
            score=analysis.get("score"),
            tags=[token.get("chain", "unknown"), token.get("dex", "unknown"), token.get("lifecycle", "unknown")],
            metrics={
                "价格": _fmt_money(token.get("price"), 8),
                "24h 涨跌": _fmt_pct(token.get("price_change_24h")),
                "流动性": _fmt_money(token.get("liquidity")),
                "市值": _fmt_money(token.get("market_cap")),
                "24h 成交量": _fmt_money(token.get("volume_24h")),
                "生命周期": str(token.get("lifecycle", "N/A")),
            },
            findings=findings,
            risks=risks,
            actions=actions,
        )

    @classmethod
    def format_audit_report(cls, audit: Dict) -> str:
        score = int(audit.get("score", 0))
        risk_level = "LOW" if score >= 85 else "MEDIUM" if score >= 70 else "HIGH"
        findings = [f"审计建议：{audit.get('recommendation', 'N/A')}"]
        findings.extend([f"命中风险：{item}" for item in audit.get("top_risks", [])])
        actions = [
            "若存在 owner/mint/blacklist 权限，默认降低仓位或放弃。",
            "在真实交易前补充源码审计与持币分布验证。",
        ]
        return cls.build_report(
            title="合约安全审计报告",
            summary="快速识别 Rug、蜜罐、权限和流动性风险。",
            score=score,
            tags=[audit.get("chain", "unknown"), risk_level, "Audit"],
            metrics={
                "合约地址": audit.get("address", "N/A"),
                "安全评分": f"{score}/100",
                "是否建议参与": "是" if audit.get("is_safe") else "否",
            },
            findings=findings,
            risks=audit.get("top_risks") or ["暂无显著风险项"],
            actions=actions,
        )

    @classmethod
    def format_address_report(cls, address: str, chain: str, activity: Dict) -> str:
        txs = activity.get("activities", [])
        recent = []
        for item in txs[:3]:
            recent.append(
                f"{item.get('type', 'tx')} | {item.get('token_in', 'N/A')} -> {item.get('token_out', 'N/A')} | gas {item.get('gas_fee', 'N/A')}"
            )
        return cls.build_report(
            title="地址画像报告",
            summary="用于识别钱包行为、常用 DEX、活跃频率与潜在聪明钱特征。",
            tags=[chain, "Address", "Intel"],
            metrics={
                "地址": address,
                "24h 交易数": str(activity.get("tx_count", 0)),
                "24h 成交量": _fmt_number(activity.get("total_24h_volume"), 2),
                "最常使用 DEX": activity.get("most_used_dex", "N/A"),
            },
            findings=["最近活动："] + recent,
            risks=["若地址标签不明，存在把普通高频地址误判为聪明钱的风险。"],
            actions=["继续结合持仓、转账对手方和跨链行为做多维验证。"],
        )

    @classmethod
    def format_trade_plan(cls, token: str, side: str, chain: str, price_data: Dict, quote: Dict, gas: Dict) -> str:
        actions = [
            f"优先按 {side} 方向制定计划，不要在高滑点环境下追价。",
            "执行前先确认 Gas、价格冲击与仓位风险是否匹配。",
            "默认采用分批入场 + 明确止损，而不是梭哈。",
        ]
        return cls.build_report(
            title=f"{token.upper()} 交易计划",
            summary="将行情、兑换报价与执行成本合并成一页可执行计划。",
            tags=[chain, side, "Trade Plan"],
            metrics={
                "现价": _fmt_money(price_data.get("price"), 6),
                "报价输出": f"{quote.get('to_amount', 0):,.6f} {quote.get('to_token', token)}",
                "价格冲击": _fmt_pct(quote.get("price_impact")),
                "建议滑点": f"{quote.get('slippage', 'N/A')}%",
                "Gas 预估": _fmt_money(gas.get("estimated_fee"), 4),
                "链": chain,
            },
            findings=[
                f"若按当前报价执行，预计可成交 {quote.get('to_amount', 0):,.6f} {quote.get('to_token', token)}。",
                f"当前 Gas 水平约为 {gas.get('gas_price', 'N/A')} {gas.get('fee_token', gas.get('unit', ''))}。",
            ],
            risks=[
                "链上报价会快速变化，特别是低流动性 token。",
                "模拟报价不等于最终成交价。",
            ],
            actions=actions,
        )
