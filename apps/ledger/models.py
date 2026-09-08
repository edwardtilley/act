from django.db import models
from django.conf import settings


class Account(models.Model):
    """Chart of accounts — 5-way classification used by the reports.

    This store (Advance) keeps its own books locally. There is no per-store
    scoping column because the ledger *is* this store's single ledger; rows are
    shared to the hub for roll-up once ``JournalEntry.hub_committed`` flips true.
    """

    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    NORMAL_BALANCES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    normal_balance = models.CharField(
        max_length=10, choices=NORMAL_BALANCES, default='debit',
        help_text="Natural balance side — debit for assets/expenses, credit for liabilities/equity/revenue",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class JournalEntry(models.Model):
    """A double-entry posting header. Debits must equal credits across its lines."""

    entry_date = models.DateField()
    description = models.CharField(max_length=500, blank=True, default='')
    reference = models.CharField(max_length=100, blank=True, default='')
    posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    # Hub roll-up sync flags — advance shares posted entries with the hub so its
    # records can roll up all stores when the hub admin wants.
    hub_committed = models.BooleanField(default=False)
    hub_pushed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-entry_date', '-id']

    def __str__(self):
        return f"Journal #{self.pk} ({self.entry_date}) — {self.description[:40]}"


class JournalLine(models.Model):
    """A single debit/credit leg of a journal entry.

    Exactly one side is nonzero — enforced by the check constraint and the
    accounting helper in views.
    """

    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='lines')
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    memo = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.journal_entry_id}: {self.account_id} D{self.debit} C{self.credit}"

    def natural_amount(self):
        """Signed amount per the account's natural balance side (debit+ / credit−)."""
        if self.account.normal_balance == 'credit':
            return self.credit - self.debit
        return self.debit - self.credit
