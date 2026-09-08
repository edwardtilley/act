"""Default chart of accounts for the Advance store ledger.

Codes follow common accounting conventions (1000s assets, 2000s liabilities,
3000s equity, 4000s revenue, 5000s expenses). ``normal_balance`` is debit for
assets/expenses and credit for liabilities/equity/revenue.
"""

DEFAULT_CHART_OF_ACCOUNTS = [
    # Assets (debit normal)
    {'code': '1000', 'name': 'Cash', 'account_type': 'asset', 'normal_balance': 'debit'},
    {'code': '1100', 'name': 'Accounts Receivable', 'account_type': 'asset', 'normal_balance': 'debit'},
    {'code': '1200', 'name': 'Inventory', 'account_type': 'asset', 'normal_balance': 'debit'},
    {'code': '1300', 'name': 'Incorporation & Legal Costs', 'account_type': 'asset', 'normal_balance': 'debit'},
    # Liabilities (credit normal)
    {'code': '2000', 'name': 'Accounts Payable', 'account_type': 'liability', 'normal_balance': 'credit'},
    {'code': '2100', 'name': 'CSQ Research Donations Payable', 'account_type': 'liability', 'normal_balance': 'credit'},
    {'code': '2300', 'name': 'Customer Deposits', 'account_type': 'liability', 'normal_balance': 'credit'},
    # Equity (credit normal)
    {'code': '3000', 'name': 'Owner / Founder Equity', 'account_type': 'equity', 'normal_balance': 'credit'},
    {'code': '3100', 'name': 'Retained Earnings', 'account_type': 'equity', 'normal_balance': 'credit'},
    # Revenue (credit normal)
    {'code': '4000', 'name': 'Donations Revenue', 'account_type': 'revenue', 'normal_balance': 'credit'},
    {'code': '4100', 'name': 'Product / Enrollment Revenue', 'account_type': 'revenue', 'normal_balance': 'credit'},
    {'code': '4200', 'name': 'Membership Revenue', 'account_type': 'revenue', 'normal_balance': 'credit'},
    # Expenses (debit normal)
    {'code': '5000', 'name': 'Incorporation & Compliance', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5100', 'name': 'Marketing & Advertising', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5200', 'name': 'Software & Hosting', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5300', 'name': 'Transaction & Processing Fees', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5400', 'name': 'Salaries & Contractors', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5500', 'name': 'Legal & Professional Services', 'account_type': 'expense', 'normal_balance': 'debit'},
    {'code': '5900', 'name': 'Other Operating Expenses', 'account_type': 'expense', 'normal_balance': 'debit'},
]


def seed_chart_of_accounts(available=('code', 'name', 'account_type', 'normal_balance'),
                           account_model=None):
    """Upsert the default COA, returning the number of accounts created/updated."""
    from .models import Account
    model = account_model or Account
    created = 0
    for item in DEFAULT_CHART_OF_ACCOUNTS:
        defaults = {k: v for k, v in item.items() if k != 'code'}
        _, was_created = model.objects.update_or_create(
            code=item['code'], defaults=defaults,
        )
        if was_created:
            created += 1
    return created
