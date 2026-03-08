"""
Lightweight OKX OnchainOS API shim.

This module provides a stable local mock so demo/CLI/Web flows run even when
real upstream APIs are unavailable.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


TOKEN_CATALOG: Dict[str, Dict[str, float]] = {
    "ETH": {"name": "Ethereum", "price": 3200.0, "market_cap": 385_000_000_000, "holders": 130_000_000},
    "WETH": {"name": "Wrapped Ether", "price": 3200.0, "market_cap": 11_000_000_000, "holders": 2_000_000},
    "BTC": {"name": "Bitcoin", "price": 95_000.0, "market_cap": 1_900_000_000_000, "holders": 55_000_000},
    "SOL": {"name": "Solana", "price": 165.0, "market_cap": 73_000_000_000, "holders": 2_500_000},
    "BNB": {"name": "BNB", "price": 470.0, "market_cap": 67_000_000_000, "holders": 1_700_000},
    "USDC": {"name": "USD Coin", "price": 1.0, "market_cap": 34_000_000_000, "holders": 7_500_000},
    "USDT": {"name": "Tether USD", "price": 1.0, "market_cap": 105_000_000_000, "holders": 6_500_000},
    "PEPE": {"name": "Pepe", "price": 0.000012, "market_cap": 5_000_000_000, "holders": 375_000},
    "WIF": {"name": "dogwifhat", "price": 2.2, "market_cap": 2_200_000_000, "holders": 145_000},
    "BONK": {"name": "Bonk", "price": 0.000028, "market_cap": 1_750_000_000, "holders": 720_000},
}

CHAIN_MULTIPLIER = {
    "ethereum": 1.0,
    "bsc": 0.999,
    "solana": 1.001,
    "base": 1.0005,
    "arbitrum": 1.0002,
    "polygon": 0.9995,
}

OPENCLAW_API_URL = os.getenv("OPENCLAW_API_URL", "http://127.0.0.1:8080")
OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "anthropic/MiniMax-M2.5")


def _iso_now() -> str:
    return datetime.now().isoformat()


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _normalize_symbol(token: str) -> str:
    token = (token or "").strip().upper()
    aliases = {
        "XETH": "ETH",
        "WBTC": "BTC",
    }
    return aliases.get(token, token or "ETH")


def _fallback_ai(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "请提供具体问题。"
    if any(k in prompt.lower() for k in ["price", "价格", "行情", "trend", "走势"]):
        return "短期波动较大，建议分批进出并严格设置止损。"
    if any(k in prompt.lower() for k in ["risk", "风险", "止损"]):
        return "先控制单笔风险在总资金 1%-2%，再考虑放大仓位。"
    return "当前未连接在线模型，已返回本地模拟建议。"


class OnchainOSClient:
    """Local-compatible client with deterministic mock outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("OKX_API_KEY")
        self.secret_key = secret_key or os.getenv("OKX_SECRET_KEY")
        self.passphrase = passphrase or os.getenv("OKX_PASSPHRASE")

    def get_price(self, token: str, chain: str = "ethereum") -> Dict:
        symbol = _normalize_symbol(token)
        record = TOKEN_CATALOG.get(symbol, {
            "name": symbol,
            "price": 1.0,
            "market_cap": 10_000_000,
            "holders": 10_000,
        })
        seed = _stable_hash(f"price:{symbol}:{chain}:{datetime.now().strftime('%Y-%m-%d-%H')}")
        drift = ((seed % 2001) - 1000) / 1000.0  # [-1, 1]
        chain_factor = CHAIN_MULTIPLIER.get(chain.lower(), 1.0)

        price = record["price"] * chain_factor * (1 + drift * 0.03)
        change_24h = drift * 7.5
        volume_24h = record["market_cap"] * (0.01 + ((seed % 300) / 10_000.0))

        return {
            "token": symbol,
            "chain": chain,
            "price": round(price, 8 if price < 1 else 6),
            "change_24h": round(change_24h, 2),
            "volume_24h": round(volume_24h, 2),
            "timestamp": _iso_now(),
        }

    def search_token(self, query: str, chain: str = "ethereum") -> Dict:
        q = (query or "").strip().lower()
        symbol = None
        for s, record in TOKEN_CATALOG.items():
            if q == s.lower() or q in record["name"].lower():
                symbol = s
                break

        if symbol is None:
            symbol = _normalize_symbol(query)[:10] or "UNKNOWN"
            record = {"name": symbol.title(), "price": 0.1, "market_cap": 25_000_000, "holders": 3_000}
        else:
            record = TOKEN_CATALOG[symbol]

        price = self.get_price(symbol, chain)
        return {
            "symbol": symbol,
            "name": record["name"],
            "chain": chain,
            "price": price["price"],
            "market_cap": int(record["market_cap"]),
            "holders": int(record["holders"]),
            "timestamp": _iso_now(),
        }

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

    def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain: str = "ethereum",
    ) -> Dict:
        amount = float(amount or 0)
        from_symbol = _normalize_symbol(from_token)
        to_symbol = _normalize_symbol(to_token)

        if amount <= 0:
            return {
                "error": "Amount must be greater than 0",
                "from_token": from_symbol,
                "to_token": to_symbol,
                "timestamp": _iso_now(),
            }

        from_price = self.get_price(from_symbol, chain)["price"]
        to_price = self.get_price(to_symbol, chain)["price"]
        gross = amount * from_price / to_price if to_price else 0

        seed = _stable_hash(f"quote:{from_symbol}:{to_symbol}:{chain}:{amount:.8f}")
        price_impact = min(4.5, 0.2 + (seed % 240) / 100.0)
        slippage = round(min(3.0, max(0.3, price_impact * 0.9)), 2)
        fee_rate = 0.003  # 0.3%
        received = gross * (1 - fee_rate - price_impact / 100.0)
        gas = self.estimate_gas(chain)

        return {
            "chain": chain,
            "from_token": from_symbol,
            "to_token": to_symbol,
            "from_amount": round(amount, 8),
            "to_amount": round(max(received, 0), 8),
            "rate": round(from_price / to_price, 10) if to_price else 0,
            "price_impact": round(price_impact, 2),
            "slippage": slippage,
            "gas_fee": gas["estimated_fee"],
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

    def estimate_gas(self, chain: str = "ethereum") -> Dict:
        base = {
            "ethereum": 22.0,
            "bsc": 3.2,
            "base": 0.7,
            "arbitrum": 0.15,
            "polygon": 48.0,
            "solana": 0.000025,
        }
        unit = "SOL" if chain == "solana" else "Gwei"
        seed = _stable_hash(f"gas:{chain}:{datetime.now().strftime('%Y-%m-%d-%H-%M')}")
        drift = ((seed % 301) - 150) / 1000.0
        gas_price = max(0.000001, base.get(chain, 20.0) * (1 + drift))

        if chain == "solana":
            estimated_fee = round(gas_price * 1.2, 6)
        else:
            eth_price = self.get_price("ETH", "ethereum")["price"]
            estimated_fee = round(gas_price * 150_000 / 1_000_000_000 * eth_price, 4)

        return {
            "chain": chain,
            "gas_price": round(gas_price, 6),
            "unit": unit,
            "estimated_fee": estimated_fee,
            "recommendation": "BUY" if gas_price < base.get(chain, 20.0) else "WAIT",
            "timestamp": _iso_now(),
        }


_client = OnchainOSClient()


def get_portfolio(address: str) -> Dict:
    return _client.get_portfolio(address)


def get_price(token: str, chain: str = "ethereum") -> Dict:
    return _client.get_price(token, chain)


def search_token(query: str, chain: str = "ethereum") -> Dict:
    return _client.search_token(query, chain)


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
    "get_portfolio",
    "get_price",
    "get_smart_money_flows",
    "get_swap_quote",
    "search_token",
]
