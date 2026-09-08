"""Admin GL pages: journal entries CRUD + Trial Balance / Balance Sheet / P&L / Cash Flow.

These are the store's own books. Only staff/superusers may view or edit.
"""

import json
import math
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .accounting import (
    compute_balance_sheet,
    compute_cash_flow,
    compute_p_and_l,
    compute_trial_balance,
    validate_and_build_entry,
)
from .models import Account, JournalEntry, JournalLine


def _staff_required(request):
    """Redirect non-staff authenticated users to the dashboard (admin-only)."""
    return redirect('/dashboard') if not (request.user.is_staff or request.user.is_superuser) else None


@login_required
def journal_entries(request):
    denied = _staff_required(request)
    if denied:
        return denied
    if request.method == 'POST':
        try:
            account_ids = request.POST.getlist('account_id[]')
            debits = request.POST.getlist('debit[]')
            credits = request.POST.getlist('credit[]')
            memos = request.POST.getlist('memo[]')
            lines, total = validate_and_build_entry(account_ids, debits, credits, memos)
            post_now = request.POST.get('post_now') == 'true'
            with transaction.atomic():
                entry = JournalEntry.objects.create(
                    entry_date=request.POST.get('entry_date') or datetime.now().date(),
                    description=request.POST.get('description', '').strip(),
                    reference=request.POST.get('reference', '').strip(),
                    posted=post_now,
                    posted_at=timezone.now() if post_now else None,
                    created_by=request.user,
                )
                for account_id, debit, credit, memo in lines:
                    JournalLine.objects.create(
                        journal_entry=entry,
                        account_id=account_id,
                        debit=debit,
                        credit=credit,
                        memo=memo,
                    )
            return redirect('/admin-financial/journal-entries')
        except ValueError as e:
            return render(request, 'ledger/journal_entries.html', {
                'segment': 'admin-financial',
                'entries': _entry_dicts(),
                'accounts': _account_dicts(),
                'error': str(e),
            })

    return render(request, 'ledger/journal_entries.html', {
        'segment': 'admin-financial',
        'entries': _entry_dicts(),
        'accounts': _account_dicts(),
    })


@login_required
def journal_entry_post(request, entry_id):
    denied = _staff_required(request)
    if denied:
        return denied
    entry = get_object_or_404(JournalEntry, pk=entry_id)
    if request.method == 'POST' and not entry.posted:
        entry.posted = True
        entry.posted_at = timezone.now()
        entry.save()
    return redirect('/admin-financial/journal-entries')


@login_required
def journal_entry_delete(request, entry_id):
    denied = _staff_required(request)
    if denied:
        return denied
    entry = get_object_or_404(JournalEntry, pk=entry_id)
    if request.method == 'POST':
        entry.delete()
    return redirect('/admin-financial/journal-entries')


@login_required
def report_trial_balance(request):
    denied = _staff_required(request)
    if denied:
        return denied
    as_of = request.GET.get('as_of') or None
    if as_of:
        try:
            as_of = datetime.strptime(as_of, '%Y-%m-%d').date()
        except ValueError:
            as_of = None
    rows = compute_trial_balance(as_of=as_of)
    total_debit = sum(r['debit_total'] for r in rows)
    total_credit = sum(r['credit_total'] for r in rows)
    total_net_debit = sum(r['net'] for r in rows if r['net'] > 0)
    total_net_credit = sum(-r['net'] for r in rows if r['net'] < 0)
    return render(request, 'ledger/trial_balance.html', {
        'segment': 'admin-financial',
        'rows': rows,
        'as_of': as_of.isoformat() if as_of else '',
        'total_debit': total_debit,
        'total_credit': total_credit,
        'total_net_debit': total_net_debit,
        'total_net_credit': total_net_credit,
    })


@login_required
def report_balance_sheet(request):
    denied = _staff_required(request)
    if denied:
        return denied
    as_of = request.GET.get('as_of') or None
    if as_of:
        try:
            as_of = datetime.strptime(as_of, '%Y-%m-%d').date()
        except ValueError:
            as_of = None
    data = compute_balance_sheet(as_of=as_of)
    data['as_of_display'] = as_of.isoformat() if as_of else ''
    data['segment'] = 'admin-financial'
    return render(request, 'ledger/balance_sheet.html', data)


@login_required
def report_p_and_l(request):
    denied = _staff_required(request)
    if denied:
        return denied
    start = request.GET.get('start_date') or None
    end = request.GET.get('end_date') or None
    s = datetime.strptime(start, '%Y-%m-%d').date() if start else None
    e = datetime.strptime(end, '%Y-%m-%d').date() if end else None
    data = compute_p_and_l(start=s, end=e)
    data['start'] = s.isoformat() if s else ''
    data['end'] = e.isoformat() if e else ''
    data['segment'] = 'admin-financial'
    return render(request, 'ledger/p_and_l.html', data)


@login_required
def report_cash_flow(request):
    denied = _staff_required(request)
    if denied:
        return denied
    start = request.GET.get('start_date') or None
    end = request.GET.get('end_date') or None
    s = datetime.strptime(start, '%Y-%m-%d').date() if start else None
    e = datetime.strptime(end, '%Y-%m-%d').date() if end else None
    data = compute_cash_flow(start=s, end=e)
    data['start'] = s.isoformat() if s else ''
    data['end'] = e.isoformat() if e else ''
    data['segment'] = 'admin-financial'
    return render(request, 'ledger/cash_flow.html', data)


def _entry_dicts():
    entries = []
    for e in JournalEntry.objects.prefetch_related('lines__account').all():
        lines = [
            {
                'id': ln.id,
                'account_id': ln.account_id,
                'debit': float(ln.debit),
                'credit': float(ln.credit),
                'memo': ln.memo,
                'account_code': ln.account.code,
                'account_name': ln.account.name,
            }
            for ln in e.lines.all()
        ]
        debit = sum(ln['debit'] for ln in lines)
        credit = sum(ln['credit'] for ln in lines)
        entries.append({
            'id': e.pk,
            'entry_date': e.entry_date.isoformat(),
            'description': e.description,
            'reference': e.reference,
            'posted': e.posted,
            'posted_at': e.posted_at.isoformat() if e.posted_at else '',
            'debit': debit,
            'credit': credit,
            'lines': lines,
        })
    return entries


def _account_dicts():
    return [
        {'id': a.id, 'code': a.code, 'name': a.name, 'account_type': a.account_type}
        for a in Account.objects.filter(is_active=True).order_by('code')
    ]
