"""Double-entry accounting helpers for the /admin/reports pages.

All report queries scope to ``journal_entry.posted == True`` (unposted drafts
are excluded from financial statements) and, where relevant, a date window.
Money is carried as Decimal; the views format to currency.
"""

from datetime import datetime

from django.db.models import Sum, F

from .models import Account, JournalEntry, JournalLine


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _totals_qs(start=None, end=None):
    """Sum debit/credit grouped by account for posted lines (optionally windowed)."""
    qs = JournalLine.objects.filter(journal_entry__posted=True)
    if start:
        qs = qs.filter(journal_entry__entry_date__gte=start)
    if end:
        qs = qs.filter(journal_entry__entry_date__lte=end)
    return qs.values('account_id').annotate(
        total_debit=Sum('debit'), total_credit=Sum('credit'),
    )


def compute_trial_balance(as_of=None):
    """Per-account debit/credit totals and signed net, sorted by account code.

    ``net`` follows the account's natural balance side: for a debit-normal
    account net = debit − credit; for credit-normal net = credit − debit.
    """
    rows = []
    totals = {r['account_id']: r for r in _totals_qs(end=as_of)}
    accounts = Account.objects.filter(is_active=True).select_related().order_by('code')
    for acc in accounts:
        t = totals.get(acc.id, {})
        debit = t.get('total_debit') or 0
        credit = t.get('total_credit') or 0
        if acc.normal_balance == 'credit':
            net = credit - debit
        else:
            net = debit - credit
        rows.append({
            'account': acc,
            'debit_total': debit,
            'credit_total': credit,
            'net': net,
        })
    return rows


def compute_balance_sheet(as_of=None):
    """Bucket trial-balance rows into assets / liabilities / equity + net income.

    Liabilities and equity are shown as positive (credit-side) figures via ``-net``.
    ``total_equity`` includes the current-period net income so that
    assets == liabilities + equity holds when the books are balanced.
    """
    rows = compute_trial_balance(as_of=as_of)
    assets, liabilities, equity = [], [], []
    revenue = 0
    expenses = 0
    for r in rows:
        acc = r['account']
        amt = r['net']
        if acc.account_type == 'asset':
            assets.append((acc, amt))
        elif acc.account_type == 'liability':
            liabilities.append((acc, -amt))
        elif acc.account_type == 'equity':
            equity.append((acc, -amt))
        elif acc.account_type == 'revenue':
            revenue += amt
        elif acc.account_type == 'expense':
            expenses += amt
    net_income = revenue - expenses
    total_assets = sum(v for _, v in assets)
    total_liabilities = sum(v for _, v in liabilities)
    total_equity = sum(v for _, v in equity)
    return {
        'as_of': as_of,
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'net_income': net_income,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity + net_income,
    }


def compute_p_and_l(start=None, end=None):
    """Revenue (credit−debit) and expense (debit−credit) accounts over a window."""
    revenues, expenses = [], []
    total_revenue = 0
    total_expense = 0
    totals = {r['account_id']: r for r in _totals_qs(start=start, end=end)}
    accounts = Account.objects.filter(is_active=True).order_by('code')
    for acc in accounts:
        t = totals.get(acc.id, {})
        debit = t.get('total_debit') or 0
        credit = t.get('total_credit') or 0
        if acc.account_type == 'revenue':
            amt = credit - debit
            revenues.append((acc, amt))
            total_revenue += amt
        elif acc.account_type == 'expense':
            amt = debit - credit
            expenses.append((acc, amt))
            total_expense += amt
    return {
        'start': start,
        'end': end,
        'revenues': revenues,
        'expenses': expenses,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'net_income': total_revenue - total_expense,
    }


def compute_cash_flow(start=None, end=None):
    """Simplified indirect-method cash statement for the Cash account (code 1000).

    Net income comes from the income statement; cash start = posted cash lines
    before ``start``; cash end = posted cash lines through ``end``.
    """
    pnl = compute_p_and_l(start=start, end=end)

    def cash_total(filter_kwargs, default=0):
        lines = JournalLine.objects.filter(
            journal_entry__posted=True, account__code='1000', **filter_kwargs,
        )
        agg = lines.aggregate(d=Sum('debit'), c=Sum('credit'))
        return (agg['d'] or 0) - (agg['c'] or 0)

    cash_start = cash_total({'journal_entry__entry_date__lt': start}) if start else None
    cash_end = cash_total({'journal_entry__entry_date__lte': end}) if end else cash_total({})
    net_change = (cash_end or 0) - (cash_start or 0) if cash_start is not None else (cash_end or 0)
    return {
        'start': start,
        'end': end,
        'net_income': pnl['net_income'],
        'cash_start': cash_start,
        'cash_end': cash_end,
        'net_change': net_change,
    }


def validate_and_build_entry(account_ids, debits, credits, memos, user=None):
    """Validate and persist a journal entry from parallel arrays.

    Returns (entry, error_string). Raises ValueError on invalid input.
    """
    if len(account_ids) != len(debits) or len(debits) != len(credits) or len(credits) != len(memos):
        raise ValueError('Mismatched line arrays.')
    lines = []
    total_debit = 0
    total_credit = 0
    for i in range(len(account_ids)):
        account_id = account_ids[i]
        if not account_id:
            raise ValueError('Every line requires an account.')
        debit = debits[i] or 0
        credit = credits[i] or 0
        try:
            debit = float(debit)
            credit = float(credit)
        except (TypeError, ValueError):
            raise ValueError('Debit/credit must be numbers.')
        if debit < 0 or credit < 0:
            raise ValueError('Debit/credit cannot be negative.')
        if debit > 0 and credit > 0:
            raise ValueError('A line cannot be both debit and credit.')
        if debit == 0 and credit == 0:
            raise ValueError('Every line needs a debit or credit amount.')
        total_debit += debit
        total_credit += credit
        lines.append((account_id, debit, credit, memos[i] if i < len(memos) else ''))
    if abs(total_debit - total_credit) >= 0.005:
        raise ValueError(
            f'Debits (${total_debit:,.2f}) and credits (${total_credit:,.2f}) must balance.'
        )
    return lines, total_debit
