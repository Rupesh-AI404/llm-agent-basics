#!/usr/bin/env python3
"""
Simple Personal Finance CLI Agent
Features:
- add income/expense
- monthly summary
- set/show budget
- export transactions to CSV
Storage: JSON file at user's home: ~/.finance_agent_data.json
"""
import argparse
import csv
import json
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List

DATA_PATH = Path.home() / ".finance_agent_data.json"

DEFAULT_DATA: Dict[str, Any] = {
    "transactions": [],  # list of {id, type, amount, category, date, note}
    "budgets": {}        # e.g. {"monthly": 2000}
}


def load_data() -> Dict[str, Any]:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_DATA.copy()
    return DEFAULT_DATA.copy()


def save_data(data: Dict[str, Any]) -> None:
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_transaction(t_type: str, amount: float, category: str, dt: str, note: str) -> None:
    data = load_data()
    try:
        parsed = datetime.fromisoformat(dt) if dt else datetime.now()
    except Exception:
        parsed = datetime.now()
    txn = {
        "id": str(uuid.uuid4()),
        "type": t_type,
        "amount": round(float(amount), 2),
        "category": category or "uncategorized",
        "date": parsed.isoformat(),
        "note": note or "",
        "budgets": {},
    }
    data.setdefault("transactions", []).append(txn)
    save_data(data)
    print(f"Added {t_type}: {txn['amount']} (category: {txn['category']})")


def set_budget(amount: float) -> None:
    data = load_data()
    data.setdefault("budgets", {})["monthly"] = round(float(amount), 2)
    save_data(data)
    print(f"Set monthly budget to: {data['budgets']['monthly']}")


def show_budget() -> None:
    data = load_data()
    b = data.get("budgets", {}).get("monthly")
    if b is None:
        print("No monthly budget set. Use 'set-budget' to set one.")
    else:
        print(f"Monthly budget: {b}")
        save_data(data)
        print(f"Set monthly budget to: {b}")


def summary(year: int, month: int) -> None:
    data = load_data()
    txns: List[Dict[str, Any]] = data.get("transactions", [])
    total_income = 0.0
    total_expense = 0.0
    by_category = {}


    for t in txns:
        try:
            tdate = datetime.fromisoformat(t["date"]) if t.get("date") else None
        except Exception:
            continue
        if tdate and tdate.year == year and tdate.month == month:
            amt = float(t.get("amount", 0))
            if t.get("type") == "income":
                total_income += amt
            else:
                total_expense += amt
                cat = t.get("category", "uncategorized")
                by_category[cat] = by_category.get(cat, 0.0) + amt

    net = total_income - total_expense
    print(f"Summary for {year}-{month:02d}")
    print(f"  Income:  {total_income:.2f}")
    print(f"  Expense: {total_expense:.2f}")
    print(f"  Net:     {net:.2f}")
    if by_category:
        print("  Expenses by category:")
        for c, v in sorted(by_category.items(), key=lambda x: -x[1]):
            print(f"    {c}: {v:.2f}")

    # Simple budget suggestion
    monthly_budget = data.get("budgets", {}).get("monthly")
    if monthly_budget is None:
        suggested_saving = total_income * 0.2
        suggested_budget = max(0.0, total_income - suggested_saving)
        print(f"\nSuggested monthly budget based on 20% savings: {suggested_budget:.2f} (save {suggested_saving:.2f})")
    else:
        remaining = monthly_budget - total_expense
        print(f"\nBudget ({monthly_budget:.2f}) remaining: {remaining:.2f}")



def export_csv(path: str) -> None:
    data = load_data()
    txns = data.get("transactions", [])
    if not txns:
        print("No transactions to export.")
        return
    fieldnames = ["id", "type", "amount", "category", "date", "note"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in txns:
            writer.writerow({k: t.get(k, "") for k in fieldnames})
    print(f"Exported {len(txns)} transactions to {path}")


def parse_args():
    p = argparse.ArgumentParser(prog="finance-agent", description="Personal finance CLI agent")
    sub = p.add_subparsers(dest="cmd")

    add = sub.add_parser("add", help="Add a transaction (income or expense)")
    add.add_argument("type", choices=["income", "expense"], help="Transaction type")
    add.add_argument("amount", type=float, help="Amount")
    add.add_argument("-c", "--category", default="uncategorized")
    add.add_argument("-d", "--date", default="", help="ISO date (YYYY-MM-DD) or empty for now")
    add.add_argument("-n", "--note", default="")

    sub.add_parser("show-budget", help="Show monthly budget")
    sb = sub.add_parser("set-budget", help="Set monthly budget")
    sb.add_argument("amount", type=float, help="Monthly budget amount")

    summ = sub.add_parser("summary", help="Show monthly summary")
    summ.add_argument("--year", type=int, default=date.today().year)
    summ.add_argument("--month", type=int, default=date.today().month)

    exp = sub.add_parser("export", help="Export all transactions to CSV")
    exp.add_argument("path", help="Output CSV path")

    return p.parse_args()


def main():
    args = parse_args()
    if args.cmd == "add":
        add_transaction(args.type, args.amount, args.category, args.date, args.note)
    elif args.cmd == "set-budget":
        set_budget(args.amount)
    elif args.cmd == "show-budget":
        show_budget()
    elif args.cmd == "summary":
        summary(args.year, args.month)
    elif args.cmd == "export":
        export_csv(args.path)
    else:
        print("No command provided. Use --help for usage.")


if __name__ == "__main__":
    main()
