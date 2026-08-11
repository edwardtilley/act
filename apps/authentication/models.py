from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    PROVINCE_CODES = ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']
    ROLE_CHOICES = [
        ('president', 'President'),
        *[(f'president_{code.lower()}', f'President {code}') for code in PROVINCE_CODES],
        ('prime_minister', 'Prime Minister'),
        ('premier', 'Premier'),
        ('leader_opposition', 'Leader of the Opposition'),
        ('mpp_leader', 'MPP Leader'),
        ('mp_leader', 'MP Leader'),
        ('member', 'Party Member'),
        ('candidate', 'Candidate'),
        ('riding_director', 'Riding Director'),
        ('treasurer', 'Treasurer'),
        ('mpp', 'MPP'),
        ('mp', 'MP'),
    ]
    CERTIFICATION_CHOICES = [
        ('', 'None'),
        ('trainee', 'Trainee (Professional Civic Scientist in training)'),
        ('graduate', 'Professional Civic Scientist (graduate)'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, blank=True, default='member')
    certification = models.CharField(
        max_length=20,
        choices=CERTIFICATION_CHOICES,
        blank=True,
        default='',
        help_text='Certified Professional Civic Scientist trainee or graduate status',
    )
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} — {self.get_role_display()}"