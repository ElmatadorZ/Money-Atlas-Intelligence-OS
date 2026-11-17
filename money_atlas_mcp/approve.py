"""Human approval for paper orders — run by a person, never by the agent.

    python -m money_atlas_mcp.approve                 # list orders awaiting approval
    python -m money_atlas_mcp.approve PA-1A2B3C       # review one, type its id to approve
    python -m money_atlas_mcp.approve PA-1A2B3C --reject
    python -m money_atlas_mcp.approve PA-1A2B3C --close 4410.5

Approval fills the paper order at the price you confirm (default: the order's entry).
Create a file named KILL in ~/.money_atlas to block all new orders and approvals.
"""
from __future__ import annotations

import argparse
import sys

from money_atlas_mcp.paper import PaperLedger, RiskError


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("order_id", nargs="?")
    p.add_argument("--reject", action="store_true")
    p.add_argument("--close", type=float, metavar="EXIT_PRICE")
    args = p.parse_args(argv)
    ledger = PaperLedger()
    if not args.order_id:
        pending = ledger.orders("awaiting_approval")["orders"]
        if not pending:
            print("No paper orders awaiting approval.")
        for o in pending:
            print(f"{o['id']}  {o['side'].upper()} {o['qty']} {o['symbol']} @ {o['entry']}  "
                  f"stop {o['stop']}  risk {o['risk_at_stop']}  — {o['rationale'][:60]}")
        return 0
    try:
        if args.reject:
            print("rejected:", ledger.reject(args.order_id)["id"])
            return 0
        if args.close is not None:
            o = ledger.close(args.order_id, args.close)
            print(f"closed {o['id']} at {o['exit_price']}: pnl {o['pnl']}")
            return 0
        o = next((x for x in ledger.orders()["orders"] if x["id"] == args.order_id), None)
        if o is None:
            print(f"no order {args.order_id}")
            return 1
        print(f"{o['side'].upper()} {o['qty']} {o['symbol']} @ {o['entry']}, stop {o['stop']}, "
              f"take-profit {o['take_profit']}, risk at stop {o['risk_at_stop']}\nRationale: {o['rationale']}")
        typed = input("Type the order id to approve (anything else cancels): ").strip()
        if typed != o["id"]:
            print("Not approved.")
            return 1
        price = input(f"Fill price [{o['entry']}]: ").strip()
        o = ledger.approve(o["id"], float(price) if price else o["entry"])
        print(f"approved {o['id']}: paper fill at {o['fill_price']}")
        return 0
    except RiskError as e:
        print(f"refused: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
