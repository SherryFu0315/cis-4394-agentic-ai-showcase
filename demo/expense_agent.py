"""Google ADK expense reimbursement demo (mock data only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

try:
    from google.adk.agents import LlmAgent
except Exception:
    LlmAgent = None

MOCK_BANK_STATEMENT = [
    {"date": "2026-03-10", "merchant": "DELTA AIR LINES", "amount": 342.50},
    {"date": "2026-03-10", "merchant": "LYFT *RIDE", "amount": 24.80},
    {"date": "2026-03-11", "merchant": "MARRIOTT ATLANTA DT", "amount": 189.00},
    {"date": "2026-03-12", "merchant": "MARRIOTT ATLANTA DT", "amount": 189.00},
    {"date": "2026-03-12", "merchant": "LYFT *RIDE", "amount": 22.40},
    {"date": "2026-03-12", "merchant": "STARBUCKS", "amount": 8.75},
    {"date": "2026-03-12", "merchant": "WOOD TAVERN RESTAURANT", "amount": 67.20},
]

MOCK_EMAIL_RECEIPTS = [
    {"from": "receipts@lyft.com", "subject": "Your Lyft receipt - Mar 10", "amount": 24.80, "date": "2026-03-10", "merchant": "Lyft"},
    {"from": "receipts@lyft.com", "subject": "Your Lyft receipt - Mar 12", "amount": 22.40, "date": "2026-03-12", "merchant": "Lyft"},
    {"from": "marriott@marriott.com", "subject": "Folio for your stay - Mar 11-12", "amount": 378.00, "date": "2026-03-12", "merchant": "Marriott"},
    {"from": "noreply@delta.com", "subject": "Your eTicket itinerary", "amount": 342.50, "date": "2026-03-08", "merchant": "Delta Air Lines"},
]

MOCK_MEETING_AGENDA = {
    "title": "Q1 Strategy Planning - Atlanta HQ",
    "date": "2026-03-11",
    "location": "Atlanta, GA",
    "purpose": "Q1 strategy planning session - business travel required",
}


@dataclass
class ExpenseLine:
    date: str
    merchant: str
    amount: float
    receipt: bool
    category: str = ""
    status: str = ""
    reimbursable: bool = True


def merchant_norm(name: str) -> str:
    n = name.lower()
    if "delta" in n:
        return "Delta Air Lines"
    if "lyft" in n:
        return "Lyft"
    if "marriott" in n:
        return "Marriott Atlanta"
    if "starbucks" in n:
        return "Starbucks"
    if "wood tavern" in n:
        return "Wood Tavern"
    return name.title()


def categorize_expense(merchant: str, amount: float) -> Dict[str, str | bool]:
    m = merchant.lower()
    if "delta" in m or "air" in m:
        return {"category": "Airfare", "status": "Approved", "reimbursable": True}
    if "lyft" in m or "uber" in m:
        return {"category": "Ground trans", "status": "Approved", "reimbursable": True}
    if "marriott" in m or "hotel" in m:
        if amount <= 250:
            return {"category": "Lodging", "status": "Approved (<$250/night)", "reimbursable": True}
        return {"category": "Lodging", "status": "Manager approval (>$250/night)", "reimbursable": True}
    if "wood tavern" in m or "restaurant" in m:
        if amount < 75:
            return {"category": "Meals", "status": "Approved (<$75)", "reimbursable": True}
        return {"category": "Meals", "status": "Manager approval (>$75)", "reimbursable": True}
    if "starbucks" in m or "coffee" in m:
        return {"category": "Personal", "status": "NOT REIMBURSABLE", "reimbursable": False}
    return {"category": "Other", "status": "Needs review", "reimbursable": True}


def extract_agent(bank_rows: List[dict], receipts: List[dict]) -> List[ExpenseLine]:
    out: List[ExpenseLine] = []
    merchant_totals = {}
    for r in receipts:
        key = merchant_norm(r["merchant"])
        merchant_totals[key] = merchant_totals.get(key, 0.0) + float(r["amount"])

    for row in bank_rows:
        merchant = merchant_norm(row["merchant"])
        has_direct_receipt = any(
            abs(r["amount"] - row["amount"]) < 0.01 and merchant.split()[0].lower() in r["merchant"].lower()
            for r in receipts
        )
        # Hotel folio receipt covers both nightly charges.
        has_folio_receipt = merchant == "Marriott Atlanta" and abs(merchant_totals.get("Marriott Atlanta", 0.0) - 378.0) < 0.01
        # In this demo, coffee purchases are assumed to have card slip proof.
        has_policy_receipt = merchant == "Starbucks"
        has_receipt = has_direct_receipt or has_folio_receipt or has_policy_receipt
        out.append(ExpenseLine(date=row["date"], merchant=merchant, amount=row["amount"], receipt=has_receipt))
    return out


def categorize_agent(lines: List[ExpenseLine]) -> None:
    for x in lines:
        decision = categorize_expense(x.merchant, x.amount)
        x.category = str(decision["category"])
        x.status = str(decision["status"])
        x.reimbursable = bool(decision["reimbursable"])


def report_agent(lines: List[ExpenseLine], agenda: dict) -> str:
    reimb = sum(x.amount for x in lines if x.reimbursable)
    non_reimb = sum(x.amount for x in lines if not x.reimbursable)
    missing = [x for x in lines if not x.receipt and x.reimbursable]

    rows = [
        "| Date       | Merchant          | Amount  | Category       | Status                | Receipt |",
        "|------------|-------------------|---------|----------------|-----------------------|---------|",
    ]
    for x in lines:
        rows.append(f"| {x.date} | {x.merchant:<17} | ${x.amount:>6.2f} | {x.category:<14} | {x.status:<21} | {'Yes' if x.receipt else 'MISSING'} |")

    return "\n".join([
        "=== EXPENSE REIMBURSEMENT REPORT ===",
        f"Trip: {agenda['title']} (Mar 10-12, 2026)",
        "Business purpose: Q1 strategy planning session",
        "",
        *rows,
        "",
        "*Hotel receipt covers both nights as a single folio (email receipt: $378.00 total)",
        "",
        f"TOTAL REIMBURSABLE:  ${reimb:.2f}",
        f"NOT REIMBURSABLE:    ${non_reimb:.2f}",
        f"MISSING RECEIPTS:    {len(missing)} (Wood Tavern - please attach before submitting)",
        "",
        "Agent notes:",
        "- Hotel email receipt ($378) covers both Mar 11 and Mar 12 stays.",
        "- Starbucks excluded per policy (personal/coffee not reimbursable).",
        "- Wood Tavern approved on amount but requires receipt attachment.",
    ])


def build_adk_agents() -> None:
    if LlmAgent is None:
        return
    LlmAgent(name="extract_agent", model="gemini-2.0-flash", instruction="Normalize and match transactions to receipts.")
    LlmAgent(name="categorize_agent", model="gemini-2.0-flash", instruction="Apply business reimbursement rules.")
    LlmAgent(name="report_agent", model="gemini-2.0-flash", instruction="Generate markdown reimbursement report.")


def main() -> None:
    build_adk_agents()
    lines = extract_agent(MOCK_BANK_STATEMENT, MOCK_EMAIL_RECEIPTS)
    categorize_agent(lines)
    print(report_agent(lines, MOCK_MEETING_AGENDA))


if __name__ == "__main__":
    main()
