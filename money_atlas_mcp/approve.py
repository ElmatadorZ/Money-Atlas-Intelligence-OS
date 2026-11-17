"""Human approval for paper orders — run by a person at a real terminal, never by the agent.

    python -m money_atlas_mcp.approve --set-passphrase   # once: choose an approval passphrase
    python -m money_atlas_mcp.approve                    # list orders awaiting approval
    python -m money_atlas_mcp.approve PA-1A2B3C          # review one, then approve with the passphrase
    python -m money_atlas_mcp.approve PA-1A2B3C --reject
    python -m money_atlas_mcp.approve PA-1A2B3C --close 4410.5
    python -m money_atlas_mcp.approve --verify           # check every approval signature

Approving needs an interactive terminal and the passphrase, which is read from the terminal
(not from piped input) and never stored — only a salted PBKDF2 hash is kept. Keep the
passphrase out of any chat. Create a file named KILL in ~/.money_atlas to block all new
orders and approvals.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from money_atlas_mcp.paper import PaperLedger, RiskError


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _ask_passphrase(prompt: str = "Approval passphrase: ") -> str:
    return getpass.getpass(prompt)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("order_id", nargs="?")
    p.add_argument("--reject", action="store_true")
    p.add_argument("--close", type=float, metavar="EXIT_PRICE")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--set-passphrase", action="store_true")
    args = p.parse_args(argv)
    ledger = PaperLedger()
    try:
        if args.set_passphrase:
            if not _interactive():
                print("refused: run this at an interactive terminal")
                return 1
            if ledger.has_passphrase():
                ledger._signing_key(_ask_passphrase("Current passphrase: "))
            new = _ask_passphrase("New passphrase (8+ characters): ")
            if new != _ask_passphrase("Repeat: "):
                print("Passphrases differ.")
                return 1
            ledger.set_passphrase(new)
            print("Approval passphrase set.")
            return 0
        if args.verify:
            res = ledger.verify(_ask_passphrase())
            print("All approvals verified." if res["ok"] else f"NOT approved through the CLI: {res['tampered']}")
            return 0 if res["ok"] else 2
        if not args.order_id:
            pending = ledger.orders("awaiting_approval")["orders"]
            if not pending:
                print("No paper orders awaiting approval.")
            for o in pending:
                print(f"{o['id']}  {o['side'].upper()} {o['qty']} {o['symbol']} @ {o['entry']}  "
                      f"stop {o['stop']}  risk {o['risk_at_stop']}  — {o['rationale'][:60]}")
            return 0
        if args.reject:
            print("rejected:", ledger.reject(args.order_id)["id"])
            return 0
        if args.close is not None:
            o = ledger.close(args.order_id, args.close)
            print(f"closed {o['id']} at {o['exit_price']}: pnl {o['pnl']}")
            return 0
        if not _interactive():
            print("refused: approval needs an interactive terminal (piped input is not accepted)")
            return 1
        o = next((x for x in ledger.orders()["orders"] if x["id"] == args.order_id), None)
        if o is None:
            print(f"no order {args.order_id}")
            return 1
        print(f"{o['side'].upper()} {o['qty']} {o['symbol']} @ {o['entry']}, stop {o['stop']}, "
              f"take-profit {o['take_profit']}, risk at stop {o['risk_at_stop']}\nRationale: {o['rationale']}")
        price = input(f"Fill price [{o['entry']}]: ").strip()
        o = ledger.approve(o["id"], float(price) if price else o["entry"], _ask_passphrase())
        print(f"approved {o['id']}: paper fill at {o['fill_price']}")
        return 0
    except (RiskError, ValueError) as e:
        print(f"refused: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
