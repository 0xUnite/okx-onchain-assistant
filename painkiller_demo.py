"""
比赛演示脚本：一键跑通痛点流程

Flow:
1) precheck
2) simulate
3) private tx strategy
4) revoke high-risk approvals (dry-run by default)
"""
from __future__ import annotations

import argparse
import json

from okx_skills.trade_guard import (
    build_private_tx_strategy,
    pre_trade_check,
    revoke_high_risk_approvals,
    simulate_trade,
)


def main():
    parser = argparse.ArgumentParser(description="Run one-click trade painkiller demo.")
    parser.add_argument("--from-token", default="ETH")
    parser.add_argument("--to-token", default="USDC")
    parser.add_argument("--amount", type=float, default=1.0)
    parser.add_argument("--chain", default="ethereum")
    parser.add_argument("--wallet", default="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    parser.add_argument("--live-revoke", action="store_true", help="Broadcast onchain revoke tx (requires EVM_PRIVATE_KEY)")
    args = parser.parse_args()

    print("=" * 72)
    print("OKX Onchain Painkiller Demo")
    print("=" * 72)

    print("\n[1] Precheck")
    check = pre_trade_check(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
        chain=args.chain,
        wallet_address=args.wallet,
    )
    print(json.dumps({"decision": check["decision"], "risk_score": check["risk_score"], "warnings": check["warnings"][:3]}, ensure_ascii=False, indent=2))

    print("\n[2] Simulate")
    sim = simulate_trade(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=args.amount,
        chain=args.chain,
        wallet_address=args.wallet,
    )
    print(json.dumps({"status": sim["status"], "expected_receive": sim["expected_receive"], "worst_case_receive": sim["worst_case_receive"]}, ensure_ascii=False, indent=2))

    print("\n[3] Private TX Strategy")
    private_tpl = build_private_tx_strategy(
        chain=args.chain,
        trade_usd=sim.get("trade_usd", 1000),
        slippage_pct=sim.get("tx_template", {}).get("max_slippage_pct", 1.0),
    )
    print(json.dumps({"mode": private_tpl["mode"], "providers": private_tpl["providers"], "template": private_tpl["template"]}, ensure_ascii=False, indent=2))

    print("\n[4] Revoke High-Risk Approvals")
    revoke = revoke_high_risk_approvals(
        wallet_address=args.wallet,
        chain=args.chain,
        execute=args.live_revoke,
        live=args.live_revoke,
    )
    subset = {
        "status": revoke.get("status"),
        "selected_count": revoke.get("selected_count"),
        "attempted": revoke.get("attempted"),
        "succeeded": revoke.get("succeeded"),
        "estimated_total_fee_usd": revoke.get("estimated_total_fee_usd"),
    }
    print(json.dumps(subset, ensure_ascii=False, indent=2))

    print("\nDone.")


if __name__ == "__main__":
    main()
