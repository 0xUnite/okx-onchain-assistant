"""
OKX OnchainOS API shim (live-first).

Design:
- Prefer live public data sources (DexScreener, GoPlus, public RPC).
- Fall back to deterministic local mock values when live endpoints are unavailable.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Dict, Iterable, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "http://127.0.0.1:8080")
OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "anthropic/MiniMax-M2.5")

DEXSCREENER_SEARCH = "https://api.dexscreener.com/latest/dex/search"
GOPLUS_TOKEN_SECURITY = "https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
GOPLUS_APPROVAL_V2 = "https://api.gopluslabs.io/api/v2/token_approval_security/{chain_id}"

# Public RPCs used for gas sampling.
CHAIN_RPC_URLS = {
    "ethereum": "https://ethereum-rpc.publicnode.com",
    "bsc": "https://bsc-dataseed.binance.org",
    "base": "https://mainnet.base.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "polygon": "https://1rpc.io/matic",
}

CHAIN_TO_GOPLUS_ID = {
    "ethereum": "1",
    "bsc": "56",
    "polygon": "137",
    "arbitrum": "42161",
    "base": "8453",
}

NATIVE_PRICE_SYMBOL = {
    "ethereum": "ETH",
    "arbitrum": "ETH",
    "base": "ETH",
    "bsc": "BNB",
    "polygon": "MATIC",
    "solana": "SOL",
}

TOKEN_CATALOG: Dict[str, Dict[str, float]] = {
    "ETH": {"name": "Ethereum", "price": 3200.0, "market_cap": 385_000_000_000, "holders": 130_000_000},
    "WETH": {"name": "Wrapped Ether", "price": 3200.0, "market_cap": 11_000_000_000, "holders": 2_000_000},
    "BTC": {"name": "Bitcoin", "price": 95_000.0, "market_cap": 1_900_000_000_000, "holders": 55_000_000},
    "SOL": {"name": "Solana", "price": 165.0, "market_cap": 73_000_000_000, "holders": 2_500_000},
    "BNB": {"name": "BNB", "price": 470.0, "market_cap": 67_000_000_000, "holders": 1_700_000},
    "MATIC": {"name": "Polygon", "price": 0.95, "market_cap": 9_000_000_000, "holders": 6_000_000},
    "USDC": {"name": "USD Coin", "price": 1.0, "market_cap": 34_000_000_000, "holders": 7_500_000},
    "USDT": {"name": "Tether USD", "price": 1.0, "market_cap": 105_000_000_000, "holders": 6_500_000},
    "PEPE": {"name": "Pepe", "price": 0.000012, "market_cap": 5_000_000_000, "holders": 375_000},
    "WIF": {"name": "dogwifhat", "price": 2.2, "market_cap": 2_200_000_000, "holders": 145_000},
    "BONK": {"name": "Bonk", "price": 0.000028, "market_cap": 1_750_000_000, "holders": 720_000},
}

# Well-known addresses for faster symbol->contract resolution.
ADDRESS_BOOK = {
    "ethereum": {
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "ETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "PEPE": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
    },
    "bsc": {
        "USDC": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
        "USDT": "0x55d398326f99059ff775485246999027b3197955",
        "WETH": "0x2170ed0880ac9a755fd29b2688956bd959f933f8",
        "ETH": "0x2170ed0880ac9a755fd29b2688956bd959f933f8",
    },
    "base": {
        "USDC": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "WETH": "0x4200000000000000000000000000000000000006",
        "ETH": "0x4200000000000000000000000000000000000006",
    },
}

CHAIN_MULTIPLIER = {
    "ethereum": 1.0,
    "bsc": 0.999,
    "solana": 1.001,
    "base": 1.0005,
    "arbitrum": 1.0002,
    "polygon": 0.9995,
}


def _iso_now() -> str:
    return datetime.now().isoformat()


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _looks_like_address(value: str) -> bool:
    value = (value or "").strip().lower()
    if not value.startswith("0x") or len(value) != 42:
        return False
    return all(ch in "0123456789abcdef" for ch in value[2:])


def _normalize_symbol(token: str) -> str:
    token = (token or "").strip().upper()
    aliases = {
        "XETH": "ETH",
        "WBTC": "BTC",
        "MATICPOL": "MATIC",
    }
    return aliases.get(token, token or "ETH")


def _fallback_ai(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "请提供具体问题。"
    lower = prompt.lower()
    if any(k in lower for k in ["price", "价格", "行情", "trend", "走势"]):
        return "短期波动较大，建议分批进出并严格设置止损。"
    if any(k in lower for k in ["risk", "风险", "止损"]):
        return "先控制单笔风险在总资金 1%-2%，再考虑放大仓位。"
    return "当前未连接在线模型，已返回本地模拟建议。"


class OnchainOSClient:
    """Live-first market/security adapter with resilient fallback behavior."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("OKX_API_KEY")
        self.secret_key = secret_key or os.getenv("OKX_SECRET_KEY")
        self.passphrase = passphrase or os.getenv("OKX_PASSPHRASE")
        self._session = requests.Session() if requests else None

    # ---------- Generic HTTP ----------

    def _http_get_json(self, url: str, params: Optional[Dict] = None, timeout: int = 12) -> Optional[Dict]:
        if not self._session:
            return None
        try:
            resp = self._session.get(url, params=params, timeout=timeout)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None

    def _http_post_json(self, url: str, payload: Dict, timeout: int = 12) -> Optional[Dict]:
        if not self._session:
            return None
        try:
            resp = self._session.post(url, json=payload, timeout=timeout)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None

    # ---------- Dex helpers ----------

    def _dex_search(self, query: str) -> List[Dict]:
        if not query:
            return []
        data = self._http_get_json(DEXSCREENER_SEARCH, params={"q": query})
        if not data:
            return []
        pairs = data.get("pairs")
        return pairs if isinstance(pairs, list) else []

    def _pair_liquidity_usd(self, pair: Dict) -> float:
        return _safe_float((pair.get("liquidity") or {}).get("usd"), 0.0)

    def _pair_volume_h24(self, pair: Dict) -> float:
        return _safe_float((pair.get("volume") or {}).get("h24"), 0.0)

    def _pair_sort_key(self, pair: Dict):
        return (self._pair_liquidity_usd(pair), self._pair_volume_h24(pair))

    def _token_matches_pair(self, pair: Dict, token: str) -> bool:
        token = (token or "").strip()
        if not token:
            return False
        is_address = _looks_like_address(token)
        token_norm = token.lower() if is_address else _normalize_symbol(token)

        base = pair.get("baseToken") or {}
        quote = pair.get("quoteToken") or {}
        if is_address:
            return token_norm in {(base.get("address") or "").lower(), (quote.get("address") or "").lower()}
        return token_norm in {
            _normalize_symbol(base.get("symbol", "")),
            _normalize_symbol(quote.get("symbol", "")),
        }

    def _filter_pairs(self, pairs: Iterable[Dict], chain: str, token: Optional[str] = None) -> List[Dict]:
        chain = (chain or "").lower()
        filtered = []
        for pair in pairs:
            if (pair.get("chainId") or "").lower() != chain:
                continue
            if token and not self._token_matches_pair(pair, token):
                continue
            filtered.append(pair)
        filtered.sort(key=self._pair_sort_key, reverse=True)
        return filtered

    def _resolve_address_from_book(self, token: str, chain: str) -> Optional[str]:
        symbol = _normalize_symbol(token)
        return (ADDRESS_BOOK.get(chain.lower(), {}) or {}).get(symbol)

    def resolve_token(self, token: str, chain: str = "ethereum") -> Dict:
        """Resolve token symbol/address from chain + identifier."""
        chain = (chain or "ethereum").lower()
        token = (token or "").strip()

        if _looks_like_address(token):
            addr = token.lower()
            pairs = self._filter_pairs(self._dex_search(addr), chain, token=addr)
            if pairs:
                pair = pairs[0]
                base = pair.get("baseToken") or {}
                quote = pair.get("quoteToken") or {}
                # Prefer exact matched side.
                side = base if (base.get("address") or "").lower() == addr else quote
                return {
                    "symbol": _normalize_symbol(side.get("symbol", token[:6])),
                    "name": side.get("name", token[:10]),
                    "address": addr,
                    "price_usd": _safe_float(pair.get("priceUsd"), 0.0),
                    "source": "dexscreener/live",
                }
            return {"symbol": token[:6].upper(), "name": token[:10], "address": addr, "price_usd": 0.0, "source": "address"}

        symbol = _normalize_symbol(token)
        known_addr = self._resolve_address_from_book(symbol, chain)
        pairs = self._filter_pairs(self._dex_search(symbol), chain, token=symbol)
        if pairs:
            pair = pairs[0]
            base = pair.get("baseToken") or {}
            quote = pair.get("quoteToken") or {}
            # Pick the side with the symbol if present, else base.
            side = base
            if _normalize_symbol(quote.get("symbol", "")) == symbol and _normalize_symbol(base.get("symbol", "")) != symbol:
                side = quote
            return {
                "symbol": _normalize_symbol(side.get("symbol", symbol)),
                "name": side.get("name", symbol),
                "address": (side.get("address") or known_addr or "").lower() or None,
                "price_usd": _safe_float(pair.get("priceUsd"), 0.0),
                "source": "dexscreener/live",
            }

        record = TOKEN_CATALOG.get(symbol, {"name": symbol, "price": 1.0})
        return {
            "symbol": symbol,
            "name": record["name"],
            "address": (known_addr or "").lower() or None,
            "price_usd": _safe_float(record.get("price"), 1.0),
            "source": "mock",
        }

    def get_market_snapshot(self, token: str, chain: str = "ethereum", max_pools: int = 5) -> Dict:
        chain = (chain or "ethereum").lower()
        token_meta = self.resolve_token(token, chain)
        pairs = self._dex_search(token_meta.get("address") or token_meta["symbol"])
        filtered = self._filter_pairs(pairs, chain, token=token_meta.get("address") or token_meta["symbol"])

        if filtered:
            top = filtered[:max_pools]
            pools = []
            for p in top:
                pools.append(
                    {
                        "dex": p.get("dexId"),
                        "pair_address": p.get("pairAddress"),
                        "price_usd": _safe_float(p.get("priceUsd"), token_meta["price_usd"]),
                        "liquidity_usd": round(self._pair_liquidity_usd(p), 2),
                        "volume_h24_usd": round(self._pair_volume_h24(p), 2),
                        "pair_created_at": p.get("pairCreatedAt"),
                    }
                )

            price_change_h24 = _safe_float((top[0].get("priceChange") or {}).get("h24"), 0.0)
            total_liq = sum(pool["liquidity_usd"] for pool in pools)
            total_vol = sum(pool["volume_h24_usd"] for pool in pools)
            price = pools[0]["price_usd"] or token_meta["price_usd"]
            return {
                "token": token_meta["symbol"],
                "token_address": token_meta.get("address"),
                "chain": chain,
                "price_usd": round(price, 8 if price < 1 else 6),
                "price_change_h24": round(price_change_h24, 2),
                "liquidity_usd": round(total_liq, 2),
                "volume_h24_usd": round(total_vol, 2),
                "pools": pools,
                "source": "dexscreener/live",
                "timestamp": _iso_now(),
            }

        # Mock fallback
        symbol = token_meta["symbol"]
        record = TOKEN_CATALOG.get(symbol, {"price": token_meta["price_usd"], "market_cap": 10_000_000})
        seed = _stable_hash(f"snapshot:{symbol}:{chain}:{datetime.now().strftime('%Y-%m-%d-%H')}")
        vol = record["market_cap"] * (0.005 + ((seed % 200) / 10_000.0))
        liq = max(vol * 2, 100_000)
        price = _safe_float(record.get("price"), 1.0)
        change = ((seed % 2001) - 1000) / 1000.0 * 5.0
        return {
            "token": symbol,
            "token_address": token_meta.get("address"),
            "chain": chain,
            "price_usd": round(price, 8 if price < 1 else 6),
            "price_change_h24": round(change, 2),
            "liquidity_usd": round(liq, 2),
            "volume_h24_usd": round(vol, 2),
            "pools": [],
            "source": "mock",
            "timestamp": _iso_now(),
        }

    # ---------- Public market APIs ----------

    def get_price(self, token: str, chain: str = "ethereum") -> Dict:
        snap = self.get_market_snapshot(token, chain, max_pools=3)
        return {
            "token": snap["token"],
            "chain": chain,
            "price": snap["price_usd"],
            "change_24h": snap["price_change_h24"],
            "volume_24h": snap["volume_h24_usd"],
            "source": snap["source"],
            "timestamp": _iso_now(),
        }

    def search_token(self, query: str, chain: str = "ethereum") -> Dict:
        chain = (chain or "ethereum").lower()
        token = self.resolve_token(query, chain)
        snap = self.get_market_snapshot(token["address"] or token["symbol"], chain, max_pools=3)

        market_cap = 0
        if snap.get("pools"):
            # DexScreener may provide fdv/marketCap by pair; if absent, leave 0.
            pairs = self._filter_pairs(self._dex_search(token["address"] or token["symbol"]), chain, token=token["address"] or token["symbol"])
            if pairs:
                market_cap = _safe_int(pairs[0].get("marketCap")) or _safe_int(pairs[0].get("fdv"))

        if market_cap <= 0:
            market_cap = _safe_int(TOKEN_CATALOG.get(token["symbol"], {}).get("market_cap"), 0)

        return {
            "symbol": token["symbol"],
            "name": token["name"],
            "chain": chain,
            "token_address": token.get("address"),
            "price": snap["price_usd"],
            "market_cap": market_cap,
            "holders": _safe_int(TOKEN_CATALOG.get(token["symbol"], {}).get("holders"), 0),
            "source": snap["source"],
            "timestamp": _iso_now(),
        }

    def get_route_snapshot(self, from_token: str, to_token: str, chain: str = "ethereum", max_routes: int = 5) -> Dict:
        chain = (chain or "ethereum").lower()
        from_meta = self.resolve_token(from_token, chain)
        to_meta = self.resolve_token(to_token, chain)

        query = f"{from_meta['symbol']} {to_meta['symbol']}"
        pairs = self._filter_pairs(self._dex_search(query), chain)

        routes = []
        for pair in pairs:
            base = pair.get("baseToken") or {}
            quote = pair.get("quoteToken") or {}
            symbols = {_normalize_symbol(base.get("symbol", "")), _normalize_symbol(quote.get("symbol", ""))}
            addrs = {(base.get("address") or "").lower(), (quote.get("address") or "").lower()}
            from_hit = from_meta["symbol"] in symbols or ((from_meta.get("address") or "") in addrs)
            to_hit = to_meta["symbol"] in symbols or ((to_meta.get("address") or "") in addrs)
            if not (from_hit and to_hit):
                continue
            routes.append(
                {
                    "dex": pair.get("dexId"),
                    "pair_address": pair.get("pairAddress"),
                    "price_usd": _safe_float(pair.get("priceUsd"), 0.0),
                    "liquidity_usd": round(self._pair_liquidity_usd(pair), 2),
                    "volume_h24_usd": round(self._pair_volume_h24(pair), 2),
                    "pair_created_at": pair.get("pairCreatedAt"),
                }
            )

        routes.sort(key=lambda r: (r["liquidity_usd"], r["volume_h24_usd"]), reverse=True)
        routes = routes[:max_routes]

        if not routes:
            return {
                "chain": chain,
                "from_token": from_meta["symbol"],
                "to_token": to_meta["symbol"],
                "routes": [],
                "best_liquidity_usd": 0.0,
                "source": "none",
                "timestamp": _iso_now(),
            }

        best_liq = routes[0]["liquidity_usd"]
        return {
            "chain": chain,
            "from_token": from_meta["symbol"],
            "to_token": to_meta["symbol"],
            "routes": routes,
            "best_liquidity_usd": best_liq,
            "source": "dexscreener/live",
            "timestamp": _iso_now(),
        }

    def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain: str = "ethereum",
    ) -> Dict:
        amount = float(amount or 0)
        chain = (chain or "ethereum").lower()
        from_meta = self.resolve_token(from_token, chain)
        to_meta = self.resolve_token(to_token, chain)

        if amount <= 0:
            return {
                "error": "Amount must be greater than 0",
                "from_token": from_meta["symbol"],
                "to_token": to_meta["symbol"],
                "timestamp": _iso_now(),
            }

        from_price = _safe_float(from_meta.get("price_usd"), 0.0) or _safe_float(self.get_price(from_meta["symbol"], chain).get("price"), 0.0)
        to_price = _safe_float(to_meta.get("price_usd"), 0.0) or _safe_float(self.get_price(to_meta["symbol"], chain).get("price"), 0.0)
        if to_price <= 0:
            return {
                "error": "Failed to resolve output token price",
                "from_token": from_meta["symbol"],
                "to_token": to_meta["symbol"],
                "timestamp": _iso_now(),
            }

        route = self.get_route_snapshot(from_token, to_token, chain)
        liquidity = _safe_float(route.get("best_liquidity_usd"), 0.0)
        trade_usd = amount * from_price

        if liquidity > 0:
            # Lightweight impact model: trade size relative to pool liquidity.
            impact = min(15.0, max(0.05, (trade_usd / max(liquidity, 1)) * 120))
            source = "live"
        else:
            seed = _stable_hash(f"quote:{from_meta['symbol']}:{to_meta['symbol']}:{chain}:{amount:.8f}")
            impact = min(4.5, 0.2 + (seed % 240) / 100.0)
            source = "mock"

        fee_rate = 0.003
        slippage = round(min(5.0, max(0.3, impact * 0.95)), 2)
        gross = trade_usd / to_price
        received = gross * (1 - fee_rate - impact / 100.0)
        gas = self.estimate_gas(chain)

        return {
            "chain": chain,
            "from_token": from_meta["symbol"],
            "to_token": to_meta["symbol"],
            "from_amount": round(amount, 8),
            "to_amount": round(max(received, 0), 8),
            "rate": round(from_price / to_price, 10) if to_price else 0,
            "price_impact": round(impact, 2),
            "slippage": slippage,
            "gas_fee": gas["estimated_fee"],
            "route_source": route.get("source"),
            "source": source,
            "timestamp": _iso_now(),
        }

    def execute_swap(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain: str = "ethereum",
        wallet_address: Optional[str] = None,
        slippage: float = 1.0,
    ) -> Dict:
        quote = self.get_swap_quote(from_token, to_token, amount, chain)
        if "error" in quote:
            return {"status": "error", **quote}

        tx_seed = f"swap:{from_token}:{to_token}:{amount}:{chain}:{wallet_address or ''}:{slippage}"
        tx_hash = f"0x{hashlib.sha256(tx_seed.encode('utf-8')).hexdigest()[:64]}"
        return {
            "status": "simulated",
            "wallet": wallet_address or "N/A",
            "tx_hash": tx_hash,
            "executed_slippage": slippage,
            "quote": quote,
            "message": "Simulated swap executed. Connect a real signer for live trading.",
            "timestamp": _iso_now(),
        }

    # ---------- Security ----------

    def get_token_security(self, token: str, chain: str = "ethereum") -> Dict:
        chain = (chain or "ethereum").lower()
        chain_id = CHAIN_TO_GOPLUS_ID.get(chain)
        token_meta = self.resolve_token(token, chain)
        address = token_meta.get("address")

        if not chain_id or not address:
            return {
                "available": False,
                "source": "none",
                "score": None,
                "risk_flags": [],
                "message": "Unsupported chain or unresolved token address",
                "timestamp": _iso_now(),
            }

        url = GOPLUS_TOKEN_SECURITY.format(chain_id=chain_id)
        data = self._http_get_json(url, params={"contract_addresses": address})
        if not data or _safe_int(data.get("code")) != 1:
            return {
                "available": False,
                "source": "goplus/error",
                "score": None,
                "risk_flags": [],
                "message": "GoPlus token security unavailable",
                "timestamp": _iso_now(),
            }

        result = data.get("result") or {}
        entry = result.get(address.lower()) or {}
        if not isinstance(entry, dict) or not entry:
            return {
                "available": False,
                "source": "goplus/empty",
                "score": None,
                "risk_flags": [],
                "message": "No token security data returned",
                "timestamp": _iso_now(),
            }

        score = 100
        risk_flags = []

        def flag(cond: bool, text: str, penalty: int):
            nonlocal score
            if cond:
                risk_flags.append(text)
                score -= penalty

        is_honeypot = entry.get("is_honeypot") == "1"
        is_open_source = entry.get("is_open_source") == "1"
        cannot_buy = entry.get("cannot_buy") == "1"
        cannot_sell_all = entry.get("cannot_sell_all") == "1"
        is_proxy = entry.get("is_proxy") == "1"
        sell_tax = _safe_float(entry.get("sell_tax"))
        buy_tax = _safe_float(entry.get("buy_tax"))

        flag(is_honeypot, "honeypot risk", 60)
        flag(cannot_buy, "cannot_buy risk", 35)
        flag(cannot_sell_all, "cannot_sell_all risk", 40)
        flag(not is_open_source, "not open source", 20)
        flag(is_proxy, "proxy contract", 8)
        flag(sell_tax > 10, f"high sell tax {sell_tax}%", 12)
        flag(buy_tax > 10, f"high buy tax {buy_tax}%", 8)
        flag(entry.get("is_in_dex") == "0", "not in dex", 10)

        score = max(0, min(100, score))
        return {
            "available": True,
            "source": "goplus/live",
            "token_address": address,
            "score": score,
            "risk_flags": risk_flags,
            "summary": {
                "is_honeypot": is_honeypot,
                "is_open_source": is_open_source,
                "is_proxy": is_proxy,
                "buy_tax": buy_tax,
                "sell_tax": sell_tax,
                "holder_count": _safe_int(entry.get("holder_count")),
            },
            "raw": entry,
            "timestamp": _iso_now(),
        }

    def _flatten_approval_items(self, result, address: str) -> List[Dict]:
        if isinstance(result, list):
            return [x for x in result if isinstance(x, dict)]
        if isinstance(result, dict):
            addr_key = (address or "").lower()
            if isinstance(result.get(addr_key), list):
                return [x for x in result.get(addr_key, []) if isinstance(x, dict)]
            items = []
            for value in result.values():
                if isinstance(value, list):
                    items.extend([x for x in value if isinstance(x, dict)])
            return items
        return []

    def _is_infinite_approval(self, item: Dict) -> bool:
        if str(item.get("is_infinite_approval", "")).lower() in {"1", "true", "yes"}:
            return True
        value_keys = ("approved_amount", "value", "allowance")
        for key in value_keys:
            value = str(item.get(key, "")).strip().lower()
            if not value:
                continue
            if value in {"unlimited", "infinite", "max"}:
                return True
            try:
                # Typical uint256 max approvals are huge (>1e30).
                if float(value) > 1e30:
                    return True
            except ValueError:
                continue
        return False

    def get_wallet_approval_risk(self, address: str, chain: str = "ethereum") -> Dict:
        chain = (chain or "ethereum").lower()
        chain_id = CHAIN_TO_GOPLUS_ID.get(chain)
        addr = (address or "").strip().lower()

        if not chain_id or not _looks_like_address(addr):
            return {
                "available": False,
                "source": "none",
                "total_approvals": 0,
                "infinite_approvals": 0,
                "risk_points": 0,
                "risk_level": "LOW",
                "items": [],
                "message": "Unsupported chain or invalid address",
                "timestamp": _iso_now(),
            }

        url = GOPLUS_APPROVAL_V2.format(chain_id=chain_id)
        data = self._http_get_json(url, params={"addresses": addr})
        if not data or _safe_int(data.get("code")) != 1:
            return {
                "available": False,
                "source": "goplus/error",
                "total_approvals": 0,
                "infinite_approvals": 0,
                "risk_points": 0,
                "risk_level": "LOW",
                "items": [],
                "message": "GoPlus approval API unavailable",
                "timestamp": _iso_now(),
            }

        items = self._flatten_approval_items(data.get("result"), addr)
        parsed = []
        infinite = 0
        risky = 0
        for item in items:
            is_infinite = self._is_infinite_approval(item)
            if is_infinite:
                infinite += 1
            is_risky = str(item.get("is_malicious", "")).lower() in {"1", "true", "yes"}
            if is_risky:
                risky += 1
            parsed.append(
                {
                    "token": item.get("token_symbol") or item.get("symbol") or "UNKNOWN",
                    "spender": item.get("spender") or item.get("approved_contract") or "N/A",
                    "approved_amount": item.get("approved_amount") or item.get("value") or item.get("allowance"),
                    "is_infinite": is_infinite,
                    "is_risky": is_risky,
                }
            )

        risk_points = infinite * 25 + risky * 25
        risk_level = "HIGH" if risk_points >= 50 else "MEDIUM" if risk_points >= 20 else "LOW"
        return {
            "available": True,
            "source": "goplus/live",
            "total_approvals": len(parsed),
            "infinite_approvals": infinite,
            "risky_approvals": risky,
            "risk_points": risk_points,
            "risk_level": risk_level,
            "items": parsed[:20],
            "timestamp": _iso_now(),
        }

    # ---------- Gas ----------

    def _rpc_gas_price_gwei(self, chain: str) -> Optional[float]:
        rpc_url = CHAIN_RPC_URLS.get(chain)
        if not rpc_url:
            return None
        result = self._http_post_json(
            rpc_url,
            payload={"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1},
            timeout=8,
        )
        if not result:
            return None
        hex_value = result.get("result")
        if not isinstance(hex_value, str) or not hex_value.startswith("0x"):
            return None
        try:
            wei = int(hex_value, 16)
            return wei / 1_000_000_000
        except ValueError:
            return None

    def estimate_gas(self, chain: str = "ethereum") -> Dict:
        chain = (chain or "ethereum").lower()
        unit = "SOL" if chain == "solana" else "Gwei"
        gas_price = self._rpc_gas_price_gwei(chain)
        source = "rpc/live"

        if gas_price is None:
            source = "mock"
            base = {
                "ethereum": 22.0,
                "bsc": 3.2,
                "base": 0.7,
                "arbitrum": 0.15,
                "polygon": 50.0,
                "solana": 0.000025,
            }
            seed = _stable_hash(f"gas:{chain}:{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
            drift = ((seed % 301) - 150) / 1000.0
            gas_price = max(0.000001, base.get(chain, 20.0) * (1 + drift))

        if chain == "solana":
            estimated_fee = round(gas_price * 1.2, 6)
        else:
            gas_limit = 150_000
            native_symbol = NATIVE_PRICE_SYMBOL.get(chain, "ETH")
            native_price = _safe_float(self.get_price(native_symbol, chain if native_symbol != "ETH" else "ethereum").get("price"), 0.0)
            if native_price <= 0:
                native_price = 3200 if native_symbol == "ETH" else TOKEN_CATALOG.get(native_symbol, {}).get("price", 1.0)
            estimated_fee = round(gas_price * gas_limit / 1_000_000_000 * native_price, 4)

        baseline = {
            "ethereum": 20,
            "bsc": 5,
            "base": 1,
            "arbitrum": 0.15,
            "polygon": 50,
            "solana": 0.00002,
        }.get(chain, 20)
        recommendation = "BUY" if gas_price < baseline else "WAIT"
        return {
            "chain": chain,
            "gas_price": round(gas_price, 6),
            "unit": unit,
            "estimated_fee": estimated_fee,
            "recommendation": recommendation,
            "source": source,
            "timestamp": _iso_now(),
        }

    # ---------- Misc ----------

    def get_portfolio(self, address: str) -> Dict:
        wallet = address or "0x0000000000000000000000000000000000000000"
        holdings = [
            ("ETH", "ethereum", 0.86),
            ("USDC", "ethereum", 1250.0),
            ("PEPE", "ethereum", 3_500_000.0),
            ("SOL", "solana", 14.2),
        ]

        assets: List[Dict] = []
        total = 0.0
        for symbol, chain, amount in holdings:
            price_data = self.get_price(symbol, chain)
            value = amount * price_data["price"]
            total += value
            assets.append(
                {
                    "chain": chain,
                    "symbol": symbol,
                    "amount": round(amount, 8),
                    "price_usd": price_data["price"],
                    "value_usd": round(value, 2),
                }
            )

        assets.sort(key=lambda a: a["value_usd"], reverse=True)
        return {
            "address": wallet,
            "total_value_usd": round(total, 2),
            "assets": assets,
            "timestamp": _iso_now(),
        }

    def get_smart_money_flows(self, chain: str = "ethereum", token: Optional[str] = None) -> Dict:
        token = _normalize_symbol(token or "ETH")
        seed = _stable_hash(f"flows:{chain}:{token}:{datetime.now().strftime('%Y-%m-%d')}")
        base = (seed % 900) + 100
        total_in = round(base * 1.3, 2)
        total_out = round(base * 0.9, 2)

        flows: List[Dict] = []
        for i in range(6):
            direction = "IN" if i % 2 == 0 else "OUT"
            amount = round((base / 12) * (1 + i * 0.1), 3)
            flows.append(
                {
                    "direction": direction,
                    "amount": amount,
                    "token": token if i % 3 else "USDC",
                    "tx_hash": f"0x{hashlib.sha256(f'{seed}:{i}'.encode('utf-8')).hexdigest()[:64]}",
                }
            )

        return {
            "chain": chain,
            "token": token,
            "total_inflow": total_in,
            "total_outflow": total_out,
            "net_flow": round(total_in - total_out, 2),
            "flows": flows,
            "timestamp": _iso_now(),
        }


_client = OnchainOSClient()


def get_portfolio(address: str) -> Dict:
    return _client.get_portfolio(address)


def get_price(token: str, chain: str = "ethereum") -> Dict:
    return _client.get_price(token, chain)


def search_token(query: str, chain: str = "ethereum") -> Dict:
    return _client.search_token(query, chain)


def get_market_snapshot(token: str, chain: str = "ethereum", max_pools: int = 5) -> Dict:
    return _client.get_market_snapshot(token, chain, max_pools)


def get_route_snapshot(from_token: str, to_token: str, chain: str = "ethereum", max_routes: int = 5) -> Dict:
    return _client.get_route_snapshot(from_token, to_token, chain, max_routes)


def get_token_security(token: str, chain: str = "ethereum") -> Dict:
    return _client.get_token_security(token, chain)


def get_wallet_approval_risk(address: str, chain: str = "ethereum") -> Dict:
    return _client.get_wallet_approval_risk(address, chain)


def get_swap_quote(from_token: str, to_token: str, amount: float, chain: str = "ethereum") -> Dict:
    return _client.get_swap_quote(from_token, to_token, amount, chain)


def execute_swap(
    from_token: str,
    to_token: str,
    amount: float,
    chain: str = "ethereum",
    wallet_address: Optional[str] = None,
    slippage: float = 1.0,
) -> Dict:
    return _client.execute_swap(from_token, to_token, amount, chain, wallet_address, slippage)


def get_smart_money_flows(chain: str = "ethereum", token: Optional[str] = None) -> Dict:
    return _client.get_smart_money_flows(chain, token)


def ask_ai(prompt: str, system_prompt: Optional[str] = None) -> str:
    if requests is None:
        return _fallback_ai(prompt)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            f"{OPENCLAW_API_URL}/v1/chat/completions",
            json={
                "model": OPENCLAW_MODEL,
                "messages": messages,
                "max_tokens": 400,
            },
            timeout=20,
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    return _fallback_ai(prompt)


__all__ = [
    "OnchainOSClient",
    "ask_ai",
    "execute_swap",
    "get_market_snapshot",
    "get_portfolio",
    "get_price",
    "get_route_snapshot",
    "get_smart_money_flows",
    "get_swap_quote",
    "get_token_security",
    "get_wallet_approval_risk",
    "search_token",
]
