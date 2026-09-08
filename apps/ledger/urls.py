from django.urls import path

from . import views

app_name = 'ledger'

# NOTE: ``/admin/`` is claimed by Django's admin site, so the GL reports live
# under /admin-financial/ to avoid being swallowed into the admin resolver.
urlpatterns = [
    path('admin-financial/journal-entries', views.journal_entries, name='journal_entries'),
    path('admin-financial/journal-entries/<int:entry_id>/post', views.journal_entry_post, name='journal_entry_post'),
    path('admin-financial/journal-entries/<int:entry_id>/delete', views.journal_entry_delete, name='journal_entry_delete'),
    path('admin-financial/reports/trial-balance', views.report_trial_balance, name='report_trial_balance'),
    path('admin-financial/reports/balance-sheet', views.report_balance_sheet, name='report_balance_sheet'),
    path('admin-financial/reports/p-and-l', views.report_p_and_l, name='report_p_and_l'),
    path('admin-financial/reports/cash-flow', views.report_cash_flow, name='report_cash_flow'),
]
