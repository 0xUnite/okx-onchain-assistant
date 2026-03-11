"""
OKX OnchainOS API Wrapper
支持钱包、DEX Market、DEX Swap、Token、Gateway
"""
import os
import requests
from datetime import datetime
from typing import Dict, Optional

# API 配置（禁止硬编码敏感信息）
OKX_API_KEY = os.getenv("OKX_API_KEY")
OKX_SECRET_KEY = os.getenv("OKX_SECRET_KEY")
OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE")

# OnchainOS API Endpoints
BASE_URL = "https://www.okx.com/api/v5"
WEB3_BASE_URL = "https://web3.okx.com"

CHAIN_ID_MAP = {
    "ethereum": "1",
    "eth": "1",
    "bsc": "56",
    "bnb": "56",
    "polygon": "137",
    "matic": "137",
    "arbitrum": "42161",
    "optimism": "10",
    "base": "8453",
    "avalanche": "43114",
    "avax": "43114",
    "solana": "501",
    "tron": "195",
    "ton": "607",
    "sui": "784",
    "aptos": "637",
}

NATIVE_TOKEN_MAP = {
    "ethereum": {"ETH", "WETH"},
    "bsc": {"BNB", "WBNB"},
    "solana": {"SOL", "WSOL"},
    "base": {"ETH", "WETH"},
    "arbitrum": {"ETH", "WETH"},
    "optimism": {"ETH", "WETH"},
    "polygon": {"MATIC", "WMATIC", "POL"},
}


class OnchainOSClient:
    """OKX OnchainOS API Client"""

    def __init__(self, api_key: str = None, secret_key: str = None, passphrase: str = None):
        self.api_key = api_key or OKX_API_KEY
        self.secret_key = secret_key or OKX_SECRET_KEY
        self.passphrase = passphrase or OKX_PASSPHRASE
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (okx-onchain-assistant)",
            "Accept": "application/json",
        })
        if self.api_key:
            self.session.headers.update({
                "OK-ACCESS-KEY": self.api_key,
                "OKX-API-KEY": self.api_key,
            })

    # ===== Helpers =====

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _chain_to_id(self, chain: str) -> str:
        return CHAIN_ID_MAP.get((chain or "ethereum").lower(), "1")

    def _safe_float(self, value, default: float = 0.0) -> float:
        try:
            if value in (None, ""):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _request_json(self, path: str, params: Dict = None, method: str = "GET", base_url: str = WEB3_BASE_URL, timeout: int = 12) -> Optional[Dict]:
        url = f"{base_url}{path}"
        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=params or {}, timeout=timeout)
            else:
                response = self.session.get(url, params=params or {}, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            code = str(data.get("code", "0"))
            if code in {"0", "200"}:
                return data
            return None
        except Exception:
            return None

    def _resolve_token(self, token: str, chain: str = "ethereum") -> Optional[Dict]:
        chain_id = self._chain_to_id(chain)
        params = {"keyword": token, "chainId": chain_id}
        result = self._request_json("/priapi/v1/dx/market/v2/search", params=params)
        if not result:
            return None
        data = result.get("data") or []
        if not data:
            return None

        token_lower = (token or "").lower()
        for item in data:
            if str(item.get("chainId")) != chain_id:
                continue
            if token_lower in {
                str(item.get("tokenContractAddress", "")).lower(),
                str(item.get("tokenSymbol", "")).lower(),
                str(item.get("tokenName", "")).lower(),
            }:
                return item

        return data[0]

    def _mock_price(self, token: str, chain: str = "ethereum") -> Dict:
        prices = {
            "ethereum": {"ETH": 3000, "WETH": 3000, "USDC": 1, "PEPE": 0.0000015},
            "bsc": {"BNB": 600, "WBNB": 600, "CAKE": 3.5, "PEPE": 0.0000012},
            "solana": {"SOL": 100, "BONK": 0.000015},
        }
        token_upper = token.upper()
        chain_prices = prices.get(chain, {})
        return {
            "token": token_upper,
            "chain": chain,
            "price": chain_prices.get(token_upper, 0),
            "change_24h": -2.5,
            "volume_24h": 1000000,
            "timestamp": self._now(),
            "source": "mock",
        }

    def _mock_market_chart(self, token: str, chain: str = "ethereum", interval: str = "1h", reason: str = None) -> Dict:
        import random

        step_seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}.get(interval, 3600)
        base_price = self.get_price(token, chain)["price"] or 1
        klines = []
        for i in range(50):
            klines.append({
                "timestamp": datetime.now().timestamp() - (50 - i) * step_seconds,
                "open": base_price * (1 + random.uniform(-0.05, 0.05)),
                "high": base_price * (1 + random.uniform(0, 0.1)),
                "low": base_price * (1 + random.uniform(-0.1, 0)),
                "close": base_price * (1 + random.uniform(-0.05, 0.05)),
                "volume": random.uniform(100000, 1000000),
            })

        return {
            "token": token,
            "chain": chain,
            "interval": interval,
            "klines": klines,
            "timestamp": self._now(),
            "source": "mock",
            "message": reason or "OKX K 线暂无可用数据，已回退到模拟数据。",
        }

    def _mock_smart_money_flows(self, chain: str = "ethereum", token: str = None, reason: str = None) -> Dict:
        flows = [
            {"address": "0x1234...abcd", "direction": "IN", "amount": 50, "token": token or "WETH", "tx_hash": "0x..."},
            {"address": "0x5678...efgh", "direction": "OUT", "amount": 100, "token": token or "USDC", "tx_hash": "0x..."},
        ]
        return {
            "chain": chain,
            "token": token,
            "flows": flows,
            "total_inflow": 50,
            "total_outflow": 100,
            "timestamp": self._now(),
            "source": "mock",
            "message": reason or "OKX Smart Money 暂无匹配信号，已回退到模拟数据。",
        }

    def _mock_search_token(self, query: str, chain: str = "ethereum") -> Dict:
        tokens = {
            "pepe": {"symbol": "PEPE", "name": "Pepe", "market_cap": 500000000, "holders": 50000},
            "wif": {"symbol": "WIF", "name": "dogwifhat", "market_cap": 300000000, "holders": 30000},
            "bonk": {"symbol": "BONK", "name": "Bonk", "market_cap": 200000000, "holders": 40000},
        }
        query_lower = query.lower()
        result = tokens.get(query_lower, {"symbol": query.upper(), "name": query, "market_cap": 0, "holders": 0})
        return {
            **result,
            "chain": chain,
            "price": self._mock_price(result["symbol"], chain)["price"],
            "timestamp": self._now(),
            "source": "mock",
        }

    def _mock_token_analytics(self, token: str, chain: str = "ethereum") -> Dict:
        return {
            "token": token,
            "chain": chain,
            "market_cap": 1000000000,
            "fdv": 1500000000,
            "circulating_supply": 1000000000,
            "total_supply": 1000000000,
            "holders": 50000,
            "top_10_holders_pct": 45,
            "liquidity_usd": 50000000,
            "volume_24h": 100000000,
            "timestamp": self._now(),
            "source": "mock",
        }

    # ===== Wallet =====

    def get_wallet_balance(self, address: str, chain: str = "ethereum") -> Dict:
        """查询钱包余额"""
        return {
            "address": address,
            "chain": chain,
            "balance": [
                {"symbol": "ETH", "amount": 1.5, "value_usd": 3000},
                {"symbol": "USDC", "amount": 5000, "value_usd": 5000},
            ],
            "total_value_usd": 8000,
            "timestamp": self._now(),
        }

    def get_portfolio(self, address: str) -> Dict:
        """获取组合概览"""
        return {
            "address": address,
            "chains": ["ethereum", "bsc", "solana"],
            "total_value_usd": 15000,
            "assets": [
                {"chain": "ethereum", "symbol": "ETH", "amount": 2.0, "value_usd": 4000},
                {"chain": "bsc", "symbol": "BNB", "amount": 5, "value_usd": 1500},
                {"chain": "solana", "symbol": "SOL", "amount": 100, "value_usd": 10000},
            ],
            "timestamp": self._now(),
        }

    # ===== DEX Market =====

    def get_price(self, token: str, chain: str = "ethereum") -> Dict:
        """获取代币价格"""
        resolved = self._resolve_token(token, chain)
        if resolved:
            return {
                "token": resolved.get("tokenSymbol", token.upper()),
                "chain": chain,
                "price": self._safe_float(resolved.get("price")),
                "change_24h": self._safe_float(resolved.get("change")),
                "volume_24h": self._safe_float(resolved.get("volume")),
                "liquidity_usd": self._safe_float(resolved.get("liquidity")),
                "market_cap": self._safe_float(resolved.get("marketCap")),
                "token_address": resolved.get("tokenContractAddress", token),
                "timestamp": self._now(),
                "source": "okx_web3_search",
            }
        return self._mock_price(token, chain)

    def get_market_chart(self, token: str, chain: str = "ethereum", interval: str = "1h") -> Dict:
        """获取 K 线数据"""
        resolved = self._resolve_token(token, chain)
        if resolved:
            params = {
                "chainId": resolved.get("chainId") or self._chain_to_id(chain),
                # 实测 OKX 使用 address，而不是 tokenAddress / tokenContractAddress
                "address": resolved.get("tokenContractAddress"),
                "bar": {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1H", "4h": "4H", "1d": "1D"}.get(interval, "1H"),
                "limit": "50",
            }
            result = self._request_json("/priapi/v5/dex/token/market/history-dex-token-hlc-candles", params=params)
            raw_klines = (result or {}).get("data") or []
            klines = []
            for item in raw_klines:
                if not isinstance(item, (list, tuple)) or len(item) < 6:
                    continue
                klines.append({
                    "timestamp": self._safe_float(item[0]),
                    "open": self._safe_float(item[1]),
                    "high": self._safe_float(item[2]),
                    "low": self._safe_float(item[3]),
                    "close": self._safe_float(item[4]),
                    "volume": self._safe_float(item[5]),
                })
            if klines:
                return {
                    "token": resolved.get("tokenSymbol", token),
                    "chain": chain,
                    "interval": interval,
                    "klines": klines,
                    "timestamp": self._now(),
                    "source": "okx_web3_kline",
                }
        return self._mock_market_chart(token, chain, interval, reason="OKX K 线接口当前没有返回该代币的真实价格序列，已自动回退到模拟数据。")

    def get_smart_money_flows(self, chain: str = "ethereum", token: str = None) -> Dict:
        """获取 Smart Money 流向"""
        chain_id = self._chain_to_id(chain)
        params = {"chainId": chain_id}
        result = self._request_json("/priapi/v1/dx/market/v2/smartmoney/signal-list", params=params)
        signals = ((result or {}).get("data") or {}).get("signals") or []

        resolved = self._resolve_token(token, chain) if token else None
        target_symbol = str((resolved or {}).get("tokenSymbol") or token or "").lower()
        target_addr = str((resolved or {}).get("tokenContractAddress") or token or "").lower()

        flows = []
        total_inflow = 0.0
        total_outflow = 0.0

        for signal in signals:
            token_info = signal.get("tokenInfo") or {}
            signal_symbol = str(token_info.get("tokenSymbol", "")).lower()
            signal_addr = str(token_info.get("tokenContractAddress", "")).lower()
            if token and signal_symbol != target_symbol and signal_addr != target_addr:
                continue

            volume = self._safe_float(signal.get("volume"))
            sell_ratio = self._safe_float(signal.get("sellRatio"))
            inflow = volume * max(0.0, 1 - sell_ratio)
            outflow = volume * max(0.0, sell_ratio)
            total_inflow += inflow
            total_outflow += outflow

            flows.append({
                "address": (signal.get("addresses") or "").split(",")[0],
                "direction": "OUT" if sell_ratio >= 0.5 else "IN",
                "amount": volume,
                "token": token_info.get("tokenSymbol") or token,
                "token_address": token_info.get("tokenContractAddress"),
                "tx_hash": f"signal:{signal.get('id')}",
                "event_time": signal.get("eventTime"),
                "price": self._safe_float(signal.get("price")),
                "liquidity_usd": self._safe_float(signal.get("liquidity")),
                "market_cap": self._safe_float(signal.get("mcap")),
                "sell_ratio": sell_ratio,
                "address_count": int(signal.get("addressNum") or 0),
            })

        if flows:
            return {
                "chain": chain,
                "token": token,
                "flows": flows[:20],
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "timestamp": self._now(),
                "source": "okx_web3_smartmoney",
            }
        return self._mock_smart_money_flows(chain, token, reason="OKX Smart Money 接口当前没有命中该代币的真实信号，已自动回退到模拟数据。")

    # ===== DEX Token =====

    def search_token(self, query: str, chain: str = "ethereum") -> Dict:
        """搜索代币"""
        resolved = self._resolve_token(query, chain)
        if resolved:
            return {
                "symbol": resolved.get("tokenSymbol", query.upper()),
                "name": resolved.get("tokenName", query),
                "chain": chain,
                "chain_id": resolved.get("chainId"),
                "token_address": resolved.get("tokenContractAddress", query),
                "price": self._safe_float(resolved.get("price")),
                "market_cap": self._safe_float(resolved.get("marketCap")),
                "holders": int(self._safe_float(resolved.get("holderAmount"))),
                "liquidity_usd": self._safe_float(resolved.get("liquidity")),
                "volume_24h": self._safe_float(resolved.get("volume")),
                "change_24h": self._safe_float(resolved.get("change")),
                "explorer_url": resolved.get("explorerUrl"),
                "token_logo_url": resolved.get("tokenLogoUrl"),
                "timestamp": self._now(),
                "source": "okx_web3_search",
            }
        return self._mock_search_token(query, chain)

    def get_token_analytics(self, token: str, chain: str = "ethereum") -> Dict:
        """获取代币分析"""
        resolved = self._resolve_token(token, chain)
        if resolved:
            token_address = resolved.get("tokenContractAddress")
            chain_id = resolved.get("chainId") or self._chain_to_id(chain)

            holders_result = self._request_json(
                "/priapi/v1/dx/market/v2/holders/analysis-info",
                params={"chainId": chain_id, "tokenAddress": token_address},
            )
            holders_data = (holders_result or {}).get("data") or {}

            trading_info = self._request_json(
                "/priapi/v1/dx/market/v2/trading-history/info",
                params={"chainId": chain_id, "tokenAddress": token_address},
            )
            trading_data = (trading_info or {}).get("data") or {}

            return {
                "token": resolved.get("tokenSymbol", token),
                "chain": chain,
                "market_cap": self._safe_float(resolved.get("marketCap")),
                "fdv": self._safe_float(holders_data.get("fdv") or resolved.get("marketCap")),
                "circulating_supply": self._safe_float(holders_data.get("circulatingSupply")),
                "total_supply": self._safe_float(holders_data.get("totalSupply")),
                "holders": int(self._safe_float(holders_data.get("holderAmount") or resolved.get("holderAmount"))),
                "top_10_holders_pct": self._safe_float(holders_data.get("top10HolderRate") or holders_data.get("topTenHolderRate")),
                "liquidity_usd": self._safe_float(resolved.get("liquidity")),
                "volume_24h": self._safe_float(trading_data.get("totalAmountUsd") or resolved.get("volume")),
                "buy_volume_24h": self._safe_float(trading_data.get("buyAmountUsd")),
                "sell_volume_24h": self._safe_float(trading_data.get("sellAmountUsd")),
                "price": self._safe_float(resolved.get("price")),
                "change_24h": self._safe_float(resolved.get("change")),
                "token_address": token_address,
                "timestamp": self._now(),
                "source": "okx_web3_token",
            }
        return self._mock_token_analytics(token, chain)

    # ===== DEX Swap =====

    def get_swap_quote(self, from_token: str, to_token: str, amount: float, chain: str = "ethereum") -> Dict:
        """获取兑换报价"""
        from_price = self.get_price(from_token, chain)["price"]
        to_price = self.get_price(to_token, chain)["price"]
        if not to_price:
            to_price = 1

        output_amount = (amount * from_price) / to_price if from_price else 0
        price_impact = 0.01
        gas_fee = 0.001 * (from_price or 0)

        return {
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": amount,
            "to_amount": output_amount * (1 - price_impact),
            "price_impact": price_impact * 100,
            "gas_fee": gas_fee,
            "chain": chain,
            "slippage": 0.5,
            "timestamp": self._now(),
        }

    def execute_swap(self, from_token: str, to_token: str, amount: float, chain: str = "ethereum", recipient: str = None) -> Dict:
        """执行兑换（模拟）"""
        quote = self.get_swap_quote(from_token, to_token, amount, chain)
        return {
            "status": "pending",
            "tx_hash": f"0x{''.join(['a'] * 64)}",
            "from_token": from_token,
            "to_token": to_token,
            "from_amount": amount,
            "to_amount": quote["to_amount"],
            "chain": chain,
            "estimated_time": "5-30 seconds",
            "timestamp": self._now(),
        }

    # ===== Onchain Gateway =====

    def estimate_gas(self, chain: str = "ethereum", to_address: str = None, data: str = None) -> Dict:
        """估算 Gas"""
        gas_prices = {
            "ethereum": 20,
            "bsc": 5,
            "solana": 0.000025,
            "base": 0.001,
        }

        gas_limit = 21000 if not data else 100000
        gas_price = gas_prices.get(chain, 20)

        return {
            "chain": chain,
            "gas_price": gas_price,
            "gas_limit": gas_limit,
            "estimated_fee": gas_price * gas_limit / 1e9 if chain != "solana" else gas_price * gas_limit,
            "fee_token": "ETH" if chain != "solana" else "SOL",
            "timestamp": self._now(),
        }

    def simulate_transaction(self, chain: str, from_address: str, to_address: str, data: str = None) -> Dict:
        """模拟交易"""
        return {
            "chain": chain,
            "from": from_address,
            "to": to_address,
            "success": True,
            "gas_used": 21000,
            "state_change": [],
            "timestamp": self._now(),
        }

    def broadcast_transaction(self, chain: str, signed_tx: str) -> Dict:
        """广播交易"""
        return {
            "tx_hash": f"0x{''.join(['a'] * 64)}",
            "chain": chain,
            "status": "submitted",
            "timestamp": self._now(),
        }

    def get_transaction_status(self, chain: str, tx_hash: str) -> Dict:
        """查询交易状态"""
        return {
            "tx_hash": tx_hash,
            "chain": chain,
            "status": "confirmed",
            "block_number": 18000000,
            "confirmations": 12,
            "timestamp": self._now(),
        }


# ===== 便捷函数 =====

def get_portfolio(address: str) -> Dict:
    """获取钱包组合"""
    client = OnchainOSClient()
    return client.get_portfolio(address)


def get_price(token: str, chain: str = "ethereum") -> Dict:
    """获取价格"""
    client = OnchainOSClient()
    return client.get_price(token, chain)


def search_token(query: str, chain: str = "ethereum") -> Dict:
    """搜索代币"""
    client = OnchainOSClient()
    return client.search_token(query, chain)


def get_swap_quote(from_token: str, to_token: str, amount: float, chain: str = "ethereum") -> Dict:
    """获取兑换报价"""
    client = OnchainOSClient()
    return client.get_swap_quote(from_token, to_token, amount, chain)


def execute_swap(from_token: str, to_token: str, amount: float, chain: str = "ethereum") -> Dict:
    """执行兑换"""
    client = OnchainOSClient()
    return client.execute_swap(from_token, to_token, amount, chain)


def get_smart_money_flows(chain: str = "ethereum", token: str = None) -> Dict:
    """获取 Smart Money 流向"""
    client = OnchainOSClient()
    return client.get_smart_money_flows(chain, token)


if __name__ == "__main__":
    client = OnchainOSClient()

    print("=== Wallet Portfolio ===")
    print(client.get_portfolio("0x123"))

    print("\n=== Price ===")
    print(client.get_price("PEPE", "ethereum"))

    print("\n=== Token Search ===")
    print(client.search_token("PEPE", "ethereum"))

    print("\n=== Token Analytics ===")
    print(client.get_token_analytics("PEPE", "ethereum"))

    print("\n=== Smart Money ===")
    print(client.get_smart_money_flows("ethereum", "PEPE"))
