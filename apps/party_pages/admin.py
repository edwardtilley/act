from django.contrib import admin
from .models import Riding, JoinApplication, Certification, CertificationApplication


@admin.register(Riding)
class RidingAdmin(admin.ModelAdmin):
    list_display = ('riding_name', 'province', 'mp_name', 'candidate_name', 'director_name', 'treasurer_name')
    list_filter = ('province', 'region', 'mp_party', 'candidate_certification')
    search_fields = ('riding_name', 'province', 'mp_name', 'candidate_name', 'director_name', 'treasurer_name')
    prepopulated_fields = {'candidate_url': ('candidate_name', 'riding_name')}
    fieldsets = (
        ('Riding', {'fields': ('riding_name', 'riding_number', 'province', 'region', 'latitude', 'longitude')}),
        ('Elected Officials', {'fields': ('mp_name', 'mp_party', 'mpp_name', 'mpp_party')}),
        ('Advance Candidate', {'fields': (
            'candidate_name', 'candidate_photo', 'candidate_certification',
            'candidate_status', 'candidate_accepted_at', 'candidate_accepted_by',
            'candidate_elected', 'candidate_bio', 'candidate_url')}),
        ('Riding Office', {'fields': (
            'director_name', 'director_photo', 'director_role',
            'treasurer_name', 'treasurer_photo', 'treasurer_role')}),
    )


@admin.register(JoinApplication)
class JoinApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_type', 'first_name', 'last_name', 'email', 'submitted_at')
    list_filter = ('application_type',)
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'level', 'active')
    list_filter = ('active', 'level')


@admin.register(CertificationApplication)
class CertificationApplicationAdmin(admin.ModelAdmin):
    list_display = ('certification', 'first_name', 'last_name', 'email', 'submitted_at')
    search_fields = ('first_name', 'last_name', 'email')
