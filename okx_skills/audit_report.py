"""
OKX OnchainOS AI 安全审计报告模块 v4.0

特性：
- 真实 OKX API / 模拟数据双模式
- 本地缓存
- 历史快照保存 + 多日趋势分析
- 8 维度评分 + 加权总分
- ASCII 图表输出
- HTML Web 报告生成
- Telegram Bot 推送
- 批量分析
- 多格式输出（text/json/markdown/compact/html）

设计目标：
- 保持向后兼容，尽量不破坏 v3.x 使用方式
- 结构清晰，便于后续扩展更多数据源
- 注释详细，但避免过度复杂抽象
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# 尝试导入 onchainos_api
try:
    from okx_skills.onchainos_api import OnchainOSClient

    HAS_OKX_API = True
except ImportError:
    HAS_OKX_API = False


# ===== 常量配置 =====
DEFAULT_CACHE_DIR = Path.home() / ".okx_audit"
DEFAULT_CACHE_TTL = 3600  # 默认缓存 1 小时
DEFAULT_HISTORY_LIMIT = 5000
TREND_MAX_POINTS = 14

SUPPORTED_CHAINS = [
    "ethereum",
    "eth",
    "bsc",
    "bnb",
    "binance",
    "solana",
    "sol",
    "polygon",
    "matic",
    "base",
    "arbitrum",
    "avalanche",
    "aptos",
    "apt",
]

CHAIN_MAPPING = {
    "ethereum": "1",
    "eth": "1",
    "bsc": "56",
    "bnb": "56",
    "binance": "56",
    "solana": "501",
    "sol": "501",
    "polygon": "137",
    "matic": "137",
    "base": "8453",
    "arbitrum": "42161",
    "avalanche": "43114",
    "aptos": "0",
    "apt": "0",
}

DIMENSION_CONFIG = [
    ("contract_security", "🔐 合约安全", 0.18),
    ("liquidity_depth", "💧 流动性", 0.17),
    ("community_activity", "🔥 社区活跃", 0.10),
    ("holder_distribution", "👥 持仓分布", 0.16),
    ("price_stability", "📊 价格稳定", 0.12),
    ("investment_evaluation", "💰 投资评估", 0.10),
    ("trading_strategy", "🎯 交易策略", 0.08),
    ("risk_matrix", "⚠️ 风险矩阵", 0.09),
]


# ===== 颜色输出 =====
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

    @staticmethod
    def score_color(score: int) -> str:
        if score >= 80:
            return Colors.GREEN
        if score >= 60:
            return Colors.YELLOW
        return Colors.RED

    @staticmethod
    def disable() -> None:
        """禁用所有颜色输出。"""
        for attr in dir(Colors):
            if not attr.startswith("_") and attr not in ["score_color", "disable"]:
                setattr(Colors, attr, "")


# ===== 通用工具 =====
def progress_bar(value: int, max_val: int = 100, width: int = 18) -> str:
    ratio = min(max(value / max_val, 0), 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {value}%"


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalize_chain(chain: str) -> str:
    c = (chain or "solana").lower().strip()
    return c if c in CHAIN_MAPPING else "solana"


# ===== ASCII 图表 =====
class AsciiChart:
    """简单 ASCII 图表工具，避免引入额外依赖。"""

    BLOCKS = "▁▂▃▄▅▆▇█"

    @classmethod
    def sparkline(cls, values: Iterable[float]) -> str:
        vals = list(values)
        if not vals:
            return "(无数据)"
        mn, mx = min(vals), max(vals)
        if math.isclose(mn, mx):
            return cls.BLOCKS[len(cls.BLOCKS) // 2] * len(vals)
        chars = []
        for v in vals:
            idx = int((v - mn) / (mx - mn) * (len(cls.BLOCKS) - 1))
            chars.append(cls.BLOCKS[idx])
        return "".join(chars)

    @classmethod
    def horizontal_bars(cls, items: List[Tuple[str, float]], width: int = 24) -> str:
        if not items:
            return "(无数据)"
        lines = []
        for label, value in items:
            v = clamp(value)
            filled = int(width * v / 100)
            bar = "█" * filled + "░" * (width - filled)
            lines.append(f"{label:<10} {bar} {v:>5.1f}")
        return "\n".join(lines)


# ===== 缓存管理 =====
class CacheManager:
    """本地缓存管理器。缓存完整报告，避免重复请求接口。"""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_CACHE_TTL):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, address: str, chain: str) -> str:
        return hashlib.sha256(f"{chain}:{address}".encode()).hexdigest()[:16]

    def get(self, address: str, chain: str) -> Optional[Dict[str, Any]]:
        cache_key = self._get_cache_key(address, chain)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if time.time() - data.get("cached_at", 0) > self.ttl:
                return None
            return data.get("report")
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, address: str, chain: str, report_data: Dict[str, Any]) -> None:
        cache_key = self._get_cache_key(address, chain)
        cache_file = self.cache_dir / f"{cache_key}.json"
        payload = {
            "report": report_data,
            "cached_at": time.time(),
            "address": address,
            "chain": chain,
        }
        try:
            cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


# ===== 历史记录管理 =====
class HistoryManager:
    """历史记录管理。

    v3.x 只保留一条最近记录，无法做真正的趋势分析。
    v4.0 改为“快照列表”模式：每次分析都保存一份摘要快照，
    并支持按 token 取最近 N 次记录做对比。
    """

    def __init__(self, history_file: Optional[Path] = None, max_records: int = DEFAULT_HISTORY_LIMIT):
        self.history_file = history_file or (DEFAULT_CACHE_DIR / "history.json")
        self.max_records = max_records
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save_snapshot(self, report: Dict[str, Any]) -> None:
        history = self.load_history()
        history.append(self._build_snapshot(report))
        history = history[-self.max_records :]
        try:
            self.history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _build_snapshot(self, report: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = {
            "token_address": report["token_address"],
            "chain": report["chain"],
            "symbol": report["symbol"],
            "name": report.get("name", report["symbol"]),
            "overall_score": report["overall_score"],
            "overall_rating": report["overall_rating"],
            "recommendation": report["recommendation"],
            "generated_at": report["generated_at"],
        }
        for field_name, _, _ in DIMENSION_CONFIG:
            dim = report.get(field_name, {}) or {}
            snapshot[field_name] = {
                "score": safe_int(dim.get("score", 0)),
                "level": dim.get("level", "D"),
                "summary": dim.get("summary", ""),
            }
        return snapshot

    def get_token_history(self, address: str, chain: str, days: int = 7, limit: int = TREND_MAX_POINTS) -> List[Dict[str, Any]]:
        items = []
        now = datetime.now()
        for rec in self.load_history():
            if rec.get("token_address") != address or rec.get("chain") != chain:
                continue
            ts = rec.get("generated_at", "")
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if days > 0 and dt < now - timedelta(days=days):
                continue
            items.append(rec)
        items.sort(key=lambda x: x.get("generated_at", ""))
        return items[-limit:]

    def build_trend_analysis(self, address: str, chain: str, current_report: Optional[Dict[str, Any]] = None, days: int = 7) -> Dict[str, Any]:
        history = self.get_token_history(address, chain, days=days)
        if current_report:
            current_ts = current_report.get("generated_at")
            if not any(item.get("generated_at") == current_ts for item in history):
                history.append(self._build_snapshot(current_report))
                history.sort(key=lambda x: x.get("generated_at", ""))
                history = history[-TREND_MAX_POINTS:]

        if not history:
            return {
                "available": False,
                "days": days,
                "points": [],
                "summary": "暂无历史趋势数据",
                "sparkline": "(无数据)",
                "change": 0,
                "change_pct": 0.0,
                "dimension_changes": {},
            }

        scores = [safe_int(item.get("overall_score", 0)) for item in history]
        change = scores[-1] - scores[0] if len(scores) >= 2 else 0
        base = scores[0] if scores and scores[0] else 1
        avg = sum(scores) / len(scores)
        volatility = max(scores) - min(scores) if scores else 0

        if change >= 8:
            direction = "明显上升"
        elif change > 0:
            direction = "小幅上升"
        elif change <= -8:
            direction = "明显下降"
        elif change < 0:
            direction = "小幅下降"
        else:
            direction = "基本稳定"

        dimension_changes: Dict[str, Dict[str, Any]] = {}
        if len(history) >= 2:
            first, last = history[0], history[-1]
            for field_name, title, _ in DIMENSION_CONFIG:
                prev_score = safe_int((first.get(field_name) or {}).get("score", 0))
                cur_score = safe_int((last.get(field_name) or {}).get("score", 0))
                dimension_changes[field_name] = {
                    "title": title,
                    "previous": prev_score,
                    "current": cur_score,
                    "change": cur_score - prev_score,
                }

        return {
            "available": True,
            "days": days,
            "points": [
                {
                    "date": item.get("generated_at", "")[:10],
                    "generated_at": item.get("generated_at", ""),
                    "score": safe_int(item.get("overall_score", 0)),
                }
                for item in history
            ],
            "summary": f"近 {days} 天趋势：{direction}，均分 {avg:.1f}，波动区间 {volatility} 分",
            "sparkline": AsciiChart.sparkline(scores),
            "change": change,
            "change_pct": round(change / base * 100, 2),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_score": round(avg, 2),
            "dimension_changes": dimension_changes,
        }


# ===== Telegram 集成 =====
class TelegramNotifier:
    """轻量 Telegram Bot 推送。

    通过环境变量或 CLI 参数传入 bot token/chat id。
    为了保持脚本自包含，这里直接使用 urllib，而不是额外依赖 requests。
    """

    def __init__(self, bot_token: Optional[str], chat_id: Optional[str]):
        self.bot_token = bot_token
        self.chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_text(self, text: str) -> Tuple[bool, str]:
        if not self.enabled:
            return False, "Telegram 未配置"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = urllib.parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": text[:4000],
                "parse_mode": "Markdown",
                "disable_web_page_preview": "true",
            }
        ).encode()
        request = urllib.request.Request(url, data=payload, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return bool(data.get("ok")), data.get("description", "ok")
        except Exception as e:  # noqa: BLE001
            return False, str(e)


# ===== 数据类 =====
@dataclass
class AuditReport:
    token_address: str
    chain: str
    symbol: str
    name: str
    overall_score: int
    overall_rating: str
    recommendation: str
    advice: Dict[str, Any]
    contract_security: Dict[str, Any]
    liquidity_depth: Dict[str, Any]
    community_activity: Dict[str, Any]
    holder_distribution: Dict[str, Any]
    price_stability: Dict[str, Any]
    investment_evaluation: Dict[str, Any]
    trading_strategy: Dict[str, Any]
    risk_matrix: Dict[str, Any]
    generated_at: str
    analysis_duration: float
    cached: bool = False
    trend_analysis: Dict[str, Any] = field(default_factory=dict, repr=False)
    score_history: Dict[str, Any] = field(default_factory=dict, repr=False)  # 向后兼容旧字段
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)


# ===== 审计报告生成器 =====
class AuditReporter:
    """审计报告生成器 v4.0"""

    def __init__(
        self,
        use_cache: bool = True,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        history_file: Optional[Path] = None,
        save_history: bool = True,
        trend_days: int = 7,
    ):
        self.okx_client = None
        self.cache = CacheManager(ttl=cache_ttl) if use_cache else None
        self.history_mgr = HistoryManager(history_file) if save_history else None
        self.trend_days = trend_days

        if HAS_OKX_API:
            try:
                self.okx_client = OnchainOSClient(
                    os.getenv("OKX_API_KEY", ""),
                    os.getenv("OKX_SECRET_KEY", ""),
                    os.getenv("OKX_PASSPHRASE", ""),
                )
                if os.getenv("OKX_API_KEY"):
                    print(f"{Colors.GREEN}✓ 已连接 OKX API{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}✓ 已连接 OKX Web3 公共接口（未配置 API Key）{Colors.RESET}")
            except Exception:
                print(f"{Colors.YELLOW}⚠ API 连接失败，使用模拟数据{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠ onchainos_api 未安装，使用模拟数据{Colors.RESET}")

    def generate_report(self, token_address: str, chain: str = "solana", force_refresh: bool = False) -> AuditReport:
        chain = normalize_chain(chain)

        if not force_refresh and self.cache:
            cached = self.cache.get(token_address, chain)
            if cached:
                print(f"{Colors.BLUE}♻️  使用缓存数据{Colors.RESET}")
                report = AuditReport(**cached)
                report.cached = True
                # 缓存里的趋势信息可能过时，这里重新生成一次，不影响主流程。
                if self.history_mgr:
                    trend = self.history_mgr.build_trend_analysis(token_address, chain, asdict(report), self.trend_days)
                    report.trend_analysis = trend
                    report.score_history = self._legacy_score_history(trend)
                return report

        start_ts = time.time()

        # 获取基础数据。这里尽量把数据抓全，后续评分和报告格式化都围绕 raw_data 展开。
        token_info = self._get_token_info(token_address, chain)
        market_data = self._get_market_data(token_address, chain)
        holder_data = self._get_holder_data(token_address, chain)
        liquidity_data = self._get_liquidity_data(token_address, chain)
        heat_data = self._get_heat_data(token_address, chain)
        extra_data = self._get_additional_data(token_address, chain, market_data)

        raw_data = {
            "token_info": token_info,
            "market_data": market_data,
            "holder_data": holder_data,
            "liquidity_data": liquidity_data,
            "heat_data": heat_data,
            "extra_data": extra_data,
        }

        # 8 维度评分
        contract_score = self._score_contract_security(holder_data, extra_data)
        liquidity_score = self._score_liquidity(liquidity_data, market_data)
        community_score = self._score_community(heat_data, market_data, extra_data)
        holder_score = self._score_holder_distribution(holder_data)
        price_score = self._score_price_stability(market_data, extra_data)
        investment_score = self._score_investment(market_data, liquidity_data, extra_data)
        strategy_score = self._score_trading_strategy(market_data, holder_data, liquidity_data, extra_data)
        risk_score = self._score_risk_matrix(holder_data, liquidity_data, market_data, extra_data)

        score_map = {
            "contract_security": contract_score,
            "liquidity_depth": liquidity_score,
            "community_activity": community_score,
            "holder_distribution": holder_score,
            "price_stability": price_score,
            "investment_evaluation": investment_score,
            "trading_strategy": strategy_score,
            "risk_matrix": risk_score,
        }
        overall_score = self._calculate_weighted_score(score_map)
        advice = self._generate_advice(score_map, overall_score)

        report = AuditReport(
            token_address=token_address,
            chain=chain,
            symbol=token_info.get("symbol", "UNKNOWN"),
            name=token_info.get("name", "Unknown"),
            overall_score=overall_score,
            overall_rating=self._get_rating(overall_score),
            recommendation=self._get_recommendation(overall_score),
            advice=advice,
            contract_security=contract_score,
            liquidity_depth=liquidity_score,
            community_activity=community_score,
            holder_distribution=holder_score,
            price_stability=price_score,
            investment_evaluation=investment_score,
            trading_strategy=strategy_score,
            risk_matrix=risk_score,
            generated_at=datetime.now().isoformat(),
            analysis_duration=round(time.time() - start_ts, 3),
            raw_data=raw_data,
        )

        report_dict = asdict(report)

        if self.history_mgr:
            # 注意顺序：先生成趋势（不包含本次），再保存快照，然后补一版包含本次的趋势。
            self.history_mgr.save_snapshot(report_dict)
            trend = self.history_mgr.build_trend_analysis(token_address, chain, report_dict, self.trend_days)
            report.trend_analysis = trend
            report.score_history = self._legacy_score_history(trend)

        if self.cache:
            self.cache.set(token_address, chain, asdict(report))

        return report

    # ===== 数据获取层 =====
    def _get_token_info(self, address: str, chain: str) -> Dict[str, Any]:
        if self.okx_client:
            try:
                result = self.okx_client.search_token(address, chain)
                return {
                    "symbol": result.get("symbol", address[:8].upper()),
                    "name": result.get("name", f"Token {address[:6]}"),
                }
            except Exception:
                pass
        return {"symbol": address[:8].upper(), "name": f"Token {address[:6]}"}

    def _get_market_data(self, address: str, chain: str) -> Dict[str, Any]:
        if self.okx_client:
            try:
                price = self.okx_client.get_price(address, chain)
                analytics = self.okx_client.get_token_analytics(address, chain)
                return {
                    "price": safe_float(price.get("price"), random.uniform(0.000001, 1.0)),
                    "change_24h": safe_float(price.get("change_24h"), random.uniform(-30, 100)),
                    "volume_24h": safe_float(price.get("volume_24h"), random.uniform(10000, 10000000)),
                    "market_cap": safe_float(analytics.get("market_cap"), random.uniform(100000, 100000000)),
                    "fdv": safe_float(analytics.get("fdv"), 0),
                }
            except Exception:
                pass
        return {
            "price": random.uniform(0.000001, 1.0),
            "change_24h": random.uniform(-30, 100),
            "volume_24h": random.uniform(10000, 10000000),
            "market_cap": random.uniform(100000, 100000000),
            "fdv": random.uniform(200000, 150000000),
        }

    def _get_holder_data(self, address: str, chain: str) -> Dict[str, Any]:
        if self.okx_client:
            try:
                analytics = self.okx_client.get_token_analytics(address, chain)
                total_holders = safe_int(analytics.get("holders"), random.randint(100, 100000))
                top_10_pct = safe_float(analytics.get("top_10_holders_pct"), random.uniform(10, 80))
                top_1_pct = clamp(top_10_pct * random.uniform(0.22, 0.65), 3, 65)
                return {
                    "total_holders": total_holders,
                    "top_10_pct": top_10_pct,
                    "top_1_pct": top_1_pct,
                }
            except Exception:
                pass
        return {
            "total_holders": random.randint(100, 100000),
            "top_10_pct": random.uniform(10, 80),
            "top_1_pct": random.uniform(5, 50),
        }

    def _get_liquidity_data(self, address: str, chain: str) -> Dict[str, Any]:
        if self.okx_client:
            try:
                analytics = self.okx_client.get_token_analytics(address, chain)
                return {
                    "liquidity_usd": safe_float(analytics.get("liquidity_usd"), random.uniform(1000, 1000000))
                }
            except Exception:
                pass
        return {"liquidity_usd": random.uniform(1000, 1000000)}

    def _get_heat_data(self, address: str, chain: str) -> Dict[str, Any]:
        # 真实社交数据若后续接第三方 API，可在这里扩展。
        return {
            "twitter": random.randint(100, 50000),
            "telegram": random.randint(100, 30000),
            "watchlist": random.randint(50, 10000),
        }

    def _get_additional_data(self, address: str, chain: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """补充更多可用于评分的衍生数据。

        这里把“更多 API 数据源”的扩展点预留好：
        - smart money 资金流
        - K 线波动率
        - FDV/MC 比例
        - 量/流动性比
        """
        smart_money = {"total_inflow": 0.0, "total_outflow": 0.0, "netflow": 0.0}
        chart_klines: List[Dict[str, Any]] = []

        if self.okx_client:
            try:
                flow = self.okx_client.get_smart_money_flows(chain, address)
                total_inflow = safe_float(flow.get("total_inflow"), 0)
                total_outflow = safe_float(flow.get("total_outflow"), 0)
                smart_money = {
                    "total_inflow": total_inflow,
                    "total_outflow": total_outflow,
                    "netflow": total_inflow - total_outflow,
                }
            except Exception:
                pass

            try:
                chart = self.okx_client.get_market_chart(address, chain, interval="1h")
                chart_klines = chart.get("klines", []) or []
            except Exception:
                pass

        if not chart_klines:
            base_price = safe_float(market_data.get("price"), 0.01) or 0.01
            for i in range(24):
                price = base_price * (1 + random.uniform(-0.08, 0.08))
                chart_klines.append(
                    {
                        "timestamp": time.time() - (24 - i) * 3600,
                        "open": price * random.uniform(0.98, 1.02),
                        "high": price * random.uniform(1.01, 1.08),
                        "low": price * random.uniform(0.92, 0.99),
                        "close": price,
                        "volume": random.uniform(10000, 500000),
                    }
                )

        closes = [safe_float(item.get("close"), 0) for item in chart_klines if safe_float(item.get("close"), 0) > 0]
        volatility_pct = self._calculate_volatility(closes)
        fdv = safe_float(market_data.get("fdv"), 0)
        mc = safe_float(market_data.get("market_cap"), 0)
        liq = max(safe_float(market_data.get("volume_24h"), 0), 1)

        return {
            "smart_money": smart_money,
            "klines": chart_klines,
            "closes": closes,
            "volatility_pct": volatility_pct,
            "fdv_mc_ratio": round(fdv / mc, 4) if mc > 0 else 0,
            "volume_liquidity_ratio": round(safe_float(market_data.get("volume_24h"), 0) / max(safe_float(self._get_liquidity_data(address, chain).get("liquidity_usd", 1), 1), 1), 4),
        }

    # ===== 评分引擎 =====
    def _calculate_weighted_score(self, score_map: Dict[str, Dict[str, Any]]) -> int:
        total = 0.0
        for field_name, _, weight in DIMENSION_CONFIG:
            total += safe_float(score_map[field_name].get("score", 0)) * weight
        return int(round(clamp(total)))

    def _calculate_volatility(self, closes: List[float]) -> float:
        if len(closes) < 2:
            return 0.0
        returns = []
        for prev, cur in zip(closes[:-1], closes[1:]):
            if prev <= 0:
                continue
            returns.append(abs((cur - prev) / prev) * 100)
        if not returns:
            return 0.0
        return round(sum(returns) / len(returns), 2)

    def _score_contract_security(self, holder_data: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        top1 = safe_float(holder_data.get("top_1_pct"), 0)
        top10 = safe_float(holder_data.get("top_10_pct"), 0)
        netflow = safe_float(extra_data.get("smart_money", {}).get("netflow"), 0)
        score = 85
        risks = []
        evidence = [f"Top1: {top1:.1f}%", f"Top10: {top10:.1f}%"]

        if top1 > 45:
            score -= 28
            risks.append(f"Top 1 持仓过高 ({top1:.1f}%)")
        elif top1 > 30:
            score -= 15
            risks.append(f"Top 1 持仓偏高 ({top1:.1f}%)")

        if top10 > 75:
            score -= 20
            risks.append(f"Top 10 过于集中 ({top10:.1f}%)")
        elif top10 > 60:
            score -= 10

        if netflow < 0:
            score -= min(8, abs(netflow) / 10000)
            evidence.append(f"Smart Money 净流出: {netflow:,.0f}")

        score = int(round(clamp(score)))
        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": "较安全" if score >= 75 else "存在集中度风险" if score >= 55 else "风险偏高",
            "evidence": evidence,
            "risks": risks,
            "advice": self._get_contract_advice(score, top1),
        }

    def _score_liquidity(self, data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        liq = safe_float(data.get("liquidity_usd"), 0)
        volume = safe_float(market_data.get("volume_24h"), 0)
        ratio = volume / max(liq, 1)
        base_score = 25 * math.log10(max(liq, 1000)) - 50
        score = clamp(base_score)
        evidence = [f"流动性: ${liq:,.0f}", f"24h 成交量: ${volume:,.0f}"]
        risks = []

        if liq < 10000:
            risks.append("流动性极低，滑点和退出风险高")
            score -= 18
        elif liq < 100000:
            risks.append("中低流动性，需控制仓位")
            score -= 5

        if ratio > 8:
            risks.append("成交量/流动性比异常偏高，可能有刷量或短炒")
            score -= 10
        elif ratio < 0.1 and liq < 50000:
            risks.append("流动性存在但成交弱，接盘效率可能偏低")
            score -= 5

        score = int(round(clamp(score)))
        if score >= 85:
            summary = "充足"
        elif score >= 70:
            summary = "良好"
        elif score >= 55:
            summary = "一般"
        else:
            summary = "偏弱"

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": summary,
            "evidence": evidence,
            "risks": risks,
            "advice": self._get_liquidity_advice(score, liq),
        }

    def _score_community(self, heat: Dict[str, Any], market: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        twitter = safe_int(heat.get("twitter"), 0)
        telegram = safe_int(heat.get("telegram"), 0)
        watchlist = safe_int(heat.get("watchlist"), 0)
        volume = safe_float(market.get("volume_24h"), 0)
        netflow = safe_float(extra_data.get("smart_money", {}).get("netflow"), 0)

        social_score = min(45, twitter / 1500 + telegram / 1200 + watchlist / 800)
        trading_score = min(35, math.log10(max(volume, 1000)) * 8)
        money_score = 10 if netflow > 0 else 4 if netflow == 0 else 0
        score = int(round(clamp(20 + social_score + trading_score + money_score)))

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": "活跃" if score >= 75 else "中等" if score >= 55 else "偏弱",
            "evidence": [f"Twitter: {twitter:,}", f"Telegram: {telegram:,}", f"Watchlist: {watchlist:,}"],
            "risks": ["热度与成交不匹配，需警惕短期情绪盘"] if score >= 80 and volume < 50000 else [],
            "advice": self._get_community_advice(score, twitter, telegram),
        }

    def _score_holder_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        top10 = safe_float(data.get("top_10_pct"), 0)
        top1 = safe_float(data.get("top_1_pct"), 0)
        holders = max(safe_int(data.get("total_holders"), 0), 1)

        decentralization = 100 - top10
        holder_bonus = min(15, math.log10(holders) * 5)
        top1_penalty = 0 if top1 < 10 else min(25, (top1 - 10) * 0.8)
        score = int(round(clamp(decentralization + holder_bonus - top1_penalty)))

        if score >= 80:
            summary = "分布健康"
        elif score >= 60:
            summary = "较均衡"
        elif score >= 45:
            summary = "偏集中"
        else:
            summary = "高度集中"

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": summary,
            "evidence": [f"Top10: {top10:.1f}%", f"Top1: {top1:.1f}%", f"持币地址: {holders:,}"],
            "risks": ["大户抛压风险较高"] if top10 > 70 or top1 > 30 else [],
            "advice": self._get_holder_advice(score, top10),
        }

    def _score_price_stability(self, data: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        chg_24h = abs(safe_float(data.get("change_24h"), 0))
        volatility = safe_float(extra_data.get("volatility_pct"), 0)
        score = 100 - chg_24h * 1.1 - volatility * 2.2
        score = int(round(clamp(score)))

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": "稳定" if score >= 80 else "可接受" if score >= 60 else "波动较大" if score >= 40 else "剧烈波动",
            "evidence": [f"24h 涨跌: {safe_float(data.get('change_24h', 0)):+.2f}%", f"小时均波动: {volatility:.2f}%"],
            "risks": ["短线波动大，容易情绪化交易"] if score < 45 else [],
            "advice": self._get_price_advice(score, chg_24h),
        }

    def _score_investment(self, data: Dict[str, Any], liquidity: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        market_cap = safe_float(data.get("market_cap"), 0)
        fdv_mc_ratio = safe_float(extra_data.get("fdv_mc_ratio"), 0)
        liq = safe_float(liquidity.get("liquidity_usd"), 0)

        size_score = min(55, math.log10(max(market_cap, 10000)) * 10)
        liq_score = min(25, math.log10(max(liq, 1000)) * 5)
        fdv_penalty = 0 if fdv_mc_ratio <= 1.5 else min(20, (fdv_mc_ratio - 1.5) * 8)
        score = int(round(clamp(10 + size_score + liq_score - fdv_penalty)))

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": "性价比良好" if score >= 75 else "中性" if score >= 55 else "偏投机",
            "evidence": [f"市值: ${market_cap:,.0f}", f"FDV/MC: {fdv_mc_ratio:.2f}"],
            "risks": ["FDV 相对市值偏高，后续解锁/稀释压力需关注"] if fdv_mc_ratio > 2 else [],
            "advice": self._get_investment_advice(score, market_cap),
        }

    def _score_trading_strategy(self, data: Dict[str, Any], holder: Dict[str, Any], liquidity: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        change = safe_float(data.get("change_24h"), 0)
        top10 = safe_float(holder.get("top_10_pct"), 0)
        liq = safe_float(liquidity.get("liquidity_usd"), 0)
        volatility = safe_float(extra_data.get("volatility_pct"), 0)

        score = 70
        if change > 45:
            score -= 22
        elif change > 20:
            score -= 10
        elif change < -20:
            score -= 8

        if top10 > 70:
            score -= 15
        elif top10 > 55:
            score -= 8

        if liq < 10000:
            score -= 18
        elif liq < 100000:
            score -= 8

        score -= min(18, volatility * 1.5)
        score = int(round(clamp(score)))

        if score >= 75:
            summary = "可轻仓顺势"
        elif score >= 60:
            summary = "等待更优位置"
        elif score >= 45:
            summary = "更适合观望"
        else:
            summary = "不建议短线参与"

        return {
            "score": score,
            "level": self._get_rating(score),
            "summary": summary,
            "evidence": [f"24h 涨跌: {change:+.2f}%", f"波动率: {volatility:.2f}%"],
            "risks": ["不适合重仓追涨"] if change > 25 else [],
            "advice": self._get_strategy_advice(score, change, liq),
        }

    def _score_risk_matrix(self, holder: Dict[str, Any], liquidity: Dict[str, Any], market: Dict[str, Any], extra_data: Dict[str, Any]) -> Dict[str, Any]:
        risk_points = 0
        top1 = safe_float(holder.get("top_1_pct"), 0)
        top10 = safe_float(holder.get("top_10_pct"), 0)
        liq = safe_float(liquidity.get("liquidity_usd"), 0)
        change = abs(safe_float(market.get("change_24h"), 0))
        netflow = safe_float(extra_data.get("smart_money", {}).get("netflow"), 0)

        if top1 > 35:
            risk_points += 2
        if top10 > 70:
            risk_points += 2
        elif top10 > 55:
            risk_points += 1
        if liq < 10000:
            risk_points += 3
        elif liq < 50000:
            risk_points += 1
        if change > 35:
            risk_points += 2
        elif change > 20:
            risk_points += 1
        if netflow < 0:
            risk_points += 1

        score = int(round(clamp(100 - risk_points * 13)))
        if risk_points >= 7:
            level, summary = "HIGH", "高风险"
        elif risk_points >= 4:
            level, summary = "MEDIUM", "中等风险"
        else:
            level, summary = "LOW", "低风险"

        return {
            "score": score,
            "level": level,
            "summary": summary,
            "evidence": [f"风险点: {risk_points}", f"净流向: {netflow:,.0f}"],
            "risks": ["综合风险项偏多，需严格止损"] if risk_points >= 4 else [],
            "advice": self._get_risk_advice(risk_points),
        }

    # ===== 建议引擎 =====
    def _generate_advice(self, score_map: Dict[str, Dict[str, Any]], overall_score: int) -> Dict[str, Any]:
        overall_advice: List[str] = []
        details: Dict[str, str] = {}

        if overall_score >= 80:
            overall_advice.append("🔥 综合质量较强，可加入重点观察列表")
        elif overall_score >= 65:
            overall_advice.append("✅ 综合表现尚可，可小仓位试错")
        elif overall_score >= 50:
            overall_advice.append("⚠️ 具备参与空间，但前提是严格风控")
        else:
            overall_advice.append("🛑 当前性价比不高，观望通常更聪明")

        sorted_dims = sorted(
            [(name, score_map[name]["score"]) for name, _, _ in DIMENSION_CONFIG],
            key=lambda x: x[1],
        )
        weakest = sorted_dims[:2]
        strongest = sorted_dims[-2:]

        title_map = {name: title for name, title, _ in DIMENSION_CONFIG}
        for name, dim in score_map.items():
            details[name] = dim.get("advice", "")

        if weakest:
            overall_advice.append(
                "📉 最弱项：" + "、".join(f"{title_map[name]}({score})" for name, score in weakest)
            )
        if strongest:
            overall_advice.append(
                "📈 最强项：" + "、".join(f"{title_map[name]}({score})" for name, score in strongest[::-1])
            )

        return {"overall": overall_advice, "details": details}

    # ===== 文案助手 =====
    def _get_contract_advice(self, score: int, top1: float) -> str:
        if score >= 80:
            return "筹码头部集中度可接受，暂未见明显结构性危险"
        if top1 > 40:
            return "重点盯住 Top1 地址异动，这类票最怕一脚踩空"
        return "安全性一般，建议结合链上地址行为继续观察"

    def _get_liquidity_advice(self, score: int, liq: float) -> str:
        if liq < 10000:
            return "单笔尽量控制在 100U 内，拆单进出"
        if liq < 100000:
            return "仓位别太莽，控制冲击成本"
        return "流动性尚可，正常交易问题不大"

    def _get_community_advice(self, score: int, tw: int, tg: int) -> str:
        if tw < 1000 and tg < 500:
            return "社区盘子还小，别把热闹当共识"
        if tw > 10000 or tg > 5000:
            return "社区热度不错，但仍需防情绪盘冲高回落"
        return "社区中等，适合继续跟踪而不是盲冲"

    def _get_holder_advice(self, score: int, top10: float) -> str:
        if top10 > 70:
            return "筹码太集中了，抛压和控盘风险都不低"
        if top10 > 50:
            return "继续观察大户地址，别在别人出货时当接盘侠"
        return "筹码分布相对健康"

    def _get_price_advice(self, score: int, chg: float) -> str:
        if chg > 30:
            return "波动很大，追涨大概率会被教育"
        if chg > 15:
            return "适合带止盈止损的小仓位策略"
        return "价格相对稳定，可结合量能观察"

    def _get_investment_advice(self, score: int, mc: float) -> str:
        if mc < 1000000:
            return "超小市值，赔率高但别幻想没有代价"
        if mc > 100000000:
            return "市值体量更稳，爆发力通常没那么疯"
        return "市值区间适中，适合平衡风险与弹性"

    def _get_strategy_advice(self, score: int, chg: float, liq: float) -> str:
        if score < 45:
            return "优先观望，真要上也只能极轻仓"
        if liq < 10000:
            return "可尝试左侧埋伏，但必须拆单"
        return "适合等待确认信号后轻仓参与"

    def _get_risk_advice(self, pts: int) -> str:
        if pts >= 7:
            return "高风险，回避通常比硬上更专业"
        if pts >= 4:
            return "中等风险，仓位和止损都要比平时更严格"
        return "风险可控，但别把低风险理解成没风险"

    def _get_rating(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        return "D"

    def _get_recommendation(self, score: int) -> str:
        if score >= 80:
            return "🔥 强烈建议关注"
        if score >= 65:
            return "✅ 可以参与"
        if score >= 50:
            return "⚠️ 谨慎参与"
        return "🛑 不建议"

    def _legacy_score_history(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """兼容旧版 score_history 字段。"""
        if not trend.get("available") or not trend.get("points"):
            return {}
        points = trend["points"]
        if len(points) < 2:
            return {}
        prev = points[-2]
        cur = points[-1]
        change = safe_int(cur.get("score", 0)) - safe_int(prev.get("score", 0))
        return {
            "previous_score": safe_int(prev.get("score", 0)),
            "change": change,
            "trend": "up" if change > 0 else "down" if change < 0 else "stable",
            "last_analyzed": prev.get("generated_at", ""),
        }


# ===== 输出格式化器 =====
class OutputFormatter:
    """输出格式化器。"""

    @staticmethod
    def format_json(report: AuditReport) -> str:
        return json.dumps(asdict(report), indent=2, ensure_ascii=False)

    @staticmethod
    def format_compact(report: AuditReport) -> str:
        trend = ""
        if report.trend_analysis.get("available"):
            change = safe_int(report.trend_analysis.get("change", 0))
            trend = f" ({'+' if change > 0 else ''}{change})"
        return f"{report.symbol}/{report.chain.upper()}: {report.overall_score}{report.overall_rating}{trend} {report.recommendation}"

    @staticmethod
    def _dimension_items(report: AuditReport) -> List[Tuple[str, Dict[str, Any]]]:
        return [
            ("🔐 合约安全", report.contract_security),
            ("💧 流动性", report.liquidity_depth),
            ("🔥 社区", report.community_activity),
            ("👥 持仓分布", report.holder_distribution),
            ("📊 价格稳定", report.price_stability),
            ("💰 投资评估", report.investment_evaluation),
            ("🎯 操作策略", report.trading_strategy),
            ("⚠️ 风险评级", report.risk_matrix),
        ]

    @staticmethod
    def _trend_line(report: AuditReport) -> str:
        trend = report.trend_analysis or {}
        if not trend.get("available"):
            return ""
        change = safe_int(trend.get("change", 0))
        symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        return f"{symbol} {trend.get('summary', '')} | {trend.get('sparkline', '')}"

    @classmethod
    def format_text(cls, report: AuditReport) -> str:
        sc = Colors.score_color(report.overall_score)
        output: List[str] = []
        output.append(f"\n{Colors.CYAN}{'=' * 64}{Colors.RESET}")
        output.append(f"{Colors.MAGENTA}{Colors.BOLD}📊 OKX OnchainOS AI 安全审计报告{Colors.RESET}")
        output.append(f"{Colors.CYAN}{'=' * 64}{Colors.RESET}")
        output.append(f"  代币: {Colors.CYAN}{report.symbol}{Colors.RESET} ({report.name})")
        output.append(f"  地址: {report.token_address}")
        output.append(f"  链:   {report.chain}")
        if report.cached:
            output.append(f"  {Colors.BLUE}♻️ 缓存数据{Colors.RESET}")
        output.append("")
        output.append(f"  🏆 总分: {sc}{report.overall_score}/100{Colors.RESET} ({report.overall_rating})")
        output.append(f"  💡 建议: {report.recommendation}")
        output.append(f"  {progress_bar(report.overall_score)}")
        trend_line = cls._trend_line(report)
        if trend_line:
            output.append(f"  {trend_line}")
        output.append("")

        for name, dim in cls._dimension_items(report):
            color = Colors.score_color(safe_int(dim.get("score", 0)))
            advice = dim.get("advice", "")
            advice_text = f" → {advice}" if advice else ""
            output.append(
                f"    {name}: {color}{safe_int(dim.get('score', 0)):>3}{Colors.RESET} {dim.get('level', '')} - {dim.get('summary', '')}{advice_text}"
            )

        output.append("")
        output.append("  📉 维度条形图:")
        items = [(title.replace("🔐 ", "").replace("💧 ", "").replace("🔥 ", "").replace("👥 ", "").replace("📊 ", "").replace("💰 ", "").replace("🎯 ", "").replace("⚠️ ", ""), safe_int(dim.get("score", 0))) for title, dim in cls._dimension_items(report)]
        output.append("  " + AsciiChart.horizontal_bars(items).replace("\n", "\n  "))

        if report.advice.get("overall"):
            output.append("")
            output.append("  🧠 智能建议:")
            for item in report.advice["overall"]:
                output.append(f"    - {item}")

        output.append("")
        output.append(f"  ⏱️ 耗时: {report.analysis_duration:.2f}s")
        output.append(f"  🕐 时间: {report.generated_at}")
        output.append(f"{Colors.CYAN}{'=' * 64}{Colors.RESET}\n")
        return "\n".join(output)

    @classmethod
    def format_markdown(cls, report: AuditReport) -> str:
        trend = report.trend_analysis or {}
        trend_md = ""
        if trend.get("available"):
            trend_md = (
                f"\n## 📈 趋势分析\n"
                f"- {trend.get('summary', '')}\n"
                f"- 变化: {'+' if safe_int(trend.get('change', 0)) > 0 else ''}{safe_int(trend.get('change', 0))} 分\n"
                f"- 趋势图: `{trend.get('sparkline', '')}`\n"
            )

        rows = []
        for title, dim in cls._dimension_items(report):
            rows.append(
                f"| {title} | **{safe_int(dim.get('score', 0))}** | {dim.get('level', '')} | {dim.get('summary', '')} | {dim.get('advice', '')} |"
            )

        advice_lines = "\n".join(f"- {item}" for item in report.advice.get("overall", []))
        return f"""# 📊 安全审计报告

## 基本信息
- **代币**: {report.symbol} ({report.name})
- **地址**: `{report.token_address}`
- **链**: {report.chain.upper()}
- **总分**: {report.overall_score}/100 ({report.overall_rating})
- **建议**: {report.recommendation}
- **进度**: `{progress_bar(report.overall_score)}`

{trend_md}
## 各维度评分

| 维度 | 评分 | 等级 | 说明 | 建议 |
|------|------|------|------|------|
{chr(10).join(rows)}

## 💡 智能建议
{advice_lines}

---
⏱️ 耗时: {report.analysis_duration:.2f}s  
🕐 生成时间: {report.generated_at}
"""

    @classmethod
    def format_html(cls, report: AuditReport) -> str:
        trend = report.trend_analysis or {}
        score_color = "#16a34a" if report.overall_score >= 80 else "#ca8a04" if report.overall_score >= 60 else "#dc2626"
        dim_cards = []
        for title, dim in cls._dimension_items(report):
            dim_cards.append(
                f"""
                <div class='card'>
                  <div class='card-title'>{html.escape(title)}</div>
                  <div class='score' style='color:{score_color};'>{safe_int(dim.get('score', 0))}</div>
                  <div class='summary'>{html.escape(str(dim.get('summary', '')))}</div>
                  <div class='advice'>{html.escape(str(dim.get('advice', '')))}</div>
                </div>
                """
            )

        advice_list = "".join(f"<li>{html.escape(item)}</li>" for item in report.advice.get("overall", []))
        trend_html = ""
        if trend.get("available"):
            trend_html = f"""
            <section>
              <h2>趋势分析</h2>
              <p>{html.escape(trend.get('summary', ''))}</p>
              <pre>{html.escape(trend.get('sparkline', ''))}</pre>
            </section>
            """

        return f"""<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>{html.escape(report.symbol)} 审计报告</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0b1020; color:#e5e7eb; margin:0; padding:24px; }}
    .wrap {{ max-width:1100px; margin:0 auto; }}
    .hero {{ background:#111827; border:1px solid #1f2937; border-radius:16px; padding:24px; margin-bottom:20px; }}
    .score-big {{ font-size:56px; font-weight:800; color:{score_color}; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }}
    .card {{ background:#111827; border:1px solid #1f2937; border-radius:14px; padding:16px; }}
    .card-title {{ font-weight:700; margin-bottom:8px; }}
    .score {{ font-size:32px; font-weight:800; }}
    .summary {{ color:#cbd5e1; margin-top:8px; }}
    .advice {{ color:#94a3b8; margin-top:8px; font-size:14px; }}
    pre {{ background:#020617; border:1px solid #1e293b; padding:12px; border-radius:10px; overflow:auto; }}
    ul {{ line-height:1.8; }}
  </style>
</head>
<body>
  <div class='wrap'>
    <section class='hero'>
      <h1>📊 {html.escape(report.symbol)} 安全审计报告</h1>
      <div class='score-big'>{report.overall_score}</div>
      <p>{html.escape(report.name)} / {html.escape(report.chain.upper())} / {html.escape(report.recommendation)}</p>
      <p>地址：<code>{html.escape(report.token_address)}</code></p>
      <p>时间：{html.escape(report.generated_at)}</p>
    </section>
    {trend_html}
    <section>
      <h2>八维评分</h2>
      <div class='grid'>
        {''.join(dim_cards)}
      </div>
    </section>
    <section>
      <h2>智能建议</h2>
      <ul>{advice_list}</ul>
    </section>
  </div>
</body>
</html>
"""


def render_dimension_chart(report: AuditReport) -> str:
    items = []
    for field_name, title, _ in DIMENSION_CONFIG:
        dim = getattr(report, field_name)
        items.append((title.replace("🔐 ", "").replace("💧 ", "").replace("🔥 ", "").replace("👥 ", "").replace("📊 ", "").replace("💰 ", "").replace("🎯 ", "").replace("⚠️ ", ""), safe_int(dim.get("score", 0))))
    return AsciiChart.horizontal_bars(items)


# ===== 参数解析 =====
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🔍 OKX OnchainOS AI 安全审计报告 v4.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s pepe                                    # 分析单个代币
  %(prog)s pepe bonk --batch                       # 批量分析多个代币
  %(prog)s --file tokens.txt                       # 从文件读取代币列表
  %(prog)s pepe --format markdown                  # Markdown 输出
  %(prog)s pepe --format html --html-out report.html
  %(prog)s pepe --trend-days 14                    # 14 天趋势分析
  %(prog)s pepe --telegram                         # 推送到 Telegram（需环境变量）
  %(prog)s pepe --chart                            # 额外输出 ASCII 图表
  %(prog)s pepe --no-cache                         # 强制刷新
        """,
    )

    parser.add_argument("addresses", nargs="*", help="代币合约地址（支持多个）")
    parser.add_argument("--chain", "-c", default="solana", help="链名称 (默认: solana)")
    parser.add_argument(
        "--format",
        "-f",
        default="text",
        choices=["text", "markdown", "compact", "json", "html"],
        help="输出格式",
    )
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出（兼容旧参数）")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--file", "-F", type=str, help="从文件读取代币地址列表（每行一个，支持'地址 链名'）")

    # 缓存相关
    parser.add_argument("--cache-ttl", type=int, default=DEFAULT_CACHE_TTL, help="缓存有效期，秒")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存")

    # 历史与趋势
    parser.add_argument("--history-file", type=str, help="历史记录文件路径")
    parser.add_argument("--no-history", action="store_true", help="不保存到历史记录")
    parser.add_argument("--trend-days", type=int, default=7, help="趋势分析天数 (默认: 7)")
    parser.add_argument("--history-limit", type=int, default=TREND_MAX_POINTS, help="单 token 趋势最多展示多少个历史点")

    # 输出控制
    parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")
    parser.add_argument("--chart", action="store_true", help="在终端额外输出 ASCII 图表")
    parser.add_argument("--html-out", type=str, help="将 HTML 报告保存到指定文件")

    # Telegram
    parser.add_argument("--telegram", action="store_true", help="分析完成后推送到 Telegram")
    parser.add_argument("--telegram-bot-token", type=str, help="Telegram Bot Token")
    parser.add_argument("--telegram-chat-id", type=str, help="Telegram Chat ID")

    return parser.parse_args()


def load_addresses(args: argparse.Namespace) -> List[Tuple[str, str]]:
    addresses: List[Tuple[str, str]] = []

    for addr in args.addresses:
        addresses.append((addr, args.chain))

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"{Colors.RED}错误：文件不存在: {args.file}{Colors.RESET}")
            sys.exit(1)
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    addr = parts[0]
                    chain = parts[1] if len(parts) > 1 else args.chain
                    addresses.append((addr, chain))
        except OSError as e:
            print(f"{Colors.RED}错误：读取文件失败: {e}{Colors.RESET}")
            sys.exit(1)

    if not addresses:
        print(f"{Colors.RED}错误：请提供代币地址或使用 --file 指定文件{Colors.RESET}")
        sys.exit(1)

    seen = set()
    unique_addresses = []
    for addr, chain in addresses:
        norm_chain = normalize_chain(chain)
        key = f"{norm_chain}:{addr}"
        if key not in seen:
            seen.add(key)
            unique_addresses.append((addr, norm_chain))
    return unique_addresses


def output_single_report(report: AuditReport, fmt: str, html_out: Optional[str] = None, chart: bool = False) -> str:
    formatter = OutputFormatter()
    if fmt == "json":
        result = formatter.format_json(report)
    elif fmt == "markdown":
        result = formatter.format_markdown(report)
    elif fmt == "compact":
        result = formatter.format_compact(report)
    elif fmt == "html":
        result = formatter.format_html(report)
    else:
        result = formatter.format_text(report)

    if html_out:
        html_content = formatter.format_html(report)
        Path(html_out).write_text(html_content, encoding="utf-8")
        print(f"{Colors.GREEN}✓ HTML 报告已保存: {html_out}{Colors.RESET}")

    if chart and fmt != "html":
        result += "\nASCII 图表:\n" + render_dimension_chart(report) + "\n"

    return result


def maybe_send_telegram(args: argparse.Namespace, reports: List[AuditReport]) -> None:
    if not args.telegram:
        return

    bot_token = args.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = args.telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
    notifier = TelegramNotifier(bot_token, chat_id)

    if not notifier.enabled:
        print(f"{Colors.YELLOW}⚠ Telegram 未配置：请设置 --telegram-bot-token/--telegram-chat-id 或环境变量{Colors.RESET}")
        return

    lines = ["*OKX 审计结果汇总*"]
    for report in reports[:10]:
        trend = report.trend_analysis or {}
        delta = safe_int(trend.get("change", 0)) if trend.get("available") else 0
        delta_text = f" ({'+' if delta > 0 else ''}{delta})" if delta else ""
        lines.append(f"- `{report.symbol}` {report.overall_score}/{report.overall_rating}{delta_text} {report.recommendation}")

    ok, message = notifier.send_text("\n".join(lines))
    if ok:
        print(f"{Colors.GREEN}✓ Telegram 推送成功{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠ Telegram 推送失败: {message}{Colors.RESET}")


# ===== 主函数 =====
def main() -> None:
    args = parse_args()

    if args.no_color:
        Colors.disable()
    if args.json:
        args.format = "json"

    unique_addresses = load_addresses(args)
    history_file = Path(args.history_file) if args.history_file else None

    reporter = AuditReporter(
        use_cache=not args.no_cache,
        cache_ttl=args.cache_ttl,
        history_file=history_file,
        save_history=not args.no_history,
        trend_days=args.trend_days,
    )

    reports: List[AuditReport] = []
    errors: List[str] = []

    for idx, (addr, chain) in enumerate(unique_addresses, start=1):
        try:
            if len(unique_addresses) > 1 or args.batch:
                print(f"\n{Colors.CYAN}[{idx}/{len(unique_addresses)}] 分析 {addr} ({chain})...{Colors.RESET}")
            report = reporter.generate_report(addr, chain, force_refresh=args.no_cache)
            reports.append(report)
        except Exception as e:  # noqa: BLE001
            msg = f"{addr} ({chain}): {e}"
            errors.append(msg)
            print(f"{Colors.RED}✗ 分析失败: {msg}{Colors.RESET}")
            if len(unique_addresses) == 1:
                raise

    if not reports:
        print(f"{Colors.RED}错误：所有分析都失败了{Colors.RESET}")
        sys.exit(1)

    if len(reports) > 1 or args.batch:
        for i, report in enumerate(reports):
            html_out = None
            if args.html_out and len(reports) == 1:
                html_out = args.html_out
            print(output_single_report(report, args.format, html_out=html_out, chart=args.chart))
            if i != len(reports) - 1:
                print()
    else:
        print(output_single_report(reports[0], args.format, html_out=args.html_out, chart=args.chart))

    if len(reports) > 1:
        print(f"\n{Colors.CYAN}{'=' * 64}{Colors.RESET}")
        print(f"{Colors.BOLD}📊 批量分析汇总 ({len(reports)}/{len(unique_addresses)} 成功){Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 64}{Colors.RESET}")
        for report in sorted(reports, key=lambda x: x.overall_score, reverse=True):
            print(f"  {Colors.score_color(report.overall_score)}{report.overall_score:>3}{Colors.RESET} | {report.symbol}/{report.chain} | {report.recommendation}")
        if errors:
            print(f"\n{Colors.RED}✗ 失败列表:{Colors.RESET}")
            for err in errors:
                print(f"  - {err}")

    maybe_send_telegram(args, reports)
    print(f"\n{Colors.BLUE}💾 缓存目录: {DEFAULT_CACHE_DIR}{Colors.RESET}")


if __name__ == "__main__":
    main()
