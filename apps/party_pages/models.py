from django.db import models


class Riding(models.Model):
    province = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    riding_name = models.CharField(max_length=255)
    riding_number = models.CharField(max_length=20, blank=True)
    mp_name = models.CharField(max_length=255, blank=True, null=True)
    mp_party = models.CharField(max_length=100, blank=True, null=True)
    mpp_name = models.CharField(max_length=255, blank=True, null=True)
    mpp_party = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    candidate_photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    candidate_bio = models.TextField(blank=True)
    candidate_url = models.SlugField(unique=True, blank=True, null=True)
    candidate_certification = models.CharField(
        max_length=20,
        choices=[('', 'None'), ('trainee', 'Trainee'), ('graduate', 'Professional Civic Scientist')],
        blank=True, default='',
        help_text="Certification level from the official's dashboard profile"
    )
    director_name = models.CharField(max_length=255, blank=True)
    director_photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    director_role = models.CharField(max_length=120, blank=True, default='Riding Director')
    treasurer_name = models.CharField(max_length=255, blank=True)
    treasurer_photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    treasurer_role = models.CharField(max_length=120, blank=True, default='Treasurer')

    class Meta:
        ordering = ['province', 'riding_name']

    def __str__(self):
        return f"{self.riding_name} ({self.province})"


class JoinApplication(models.Model):
    APPLICATION_TYPES = [
        ('candidate', 'Candidate'),
        ('member', 'Party Member'),
    ]
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application_type}: {self.first_name} {self.last_name}"


class Certification(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class StatImage(models.Model):
    title = models.CharField(max_length=255)
    image_filename = models.CharField(max_length=255, help_text="Filename from static/assets/img/ or media/")
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True, help_text="Comma-delimited keywords for filtering")
    links_json = models.TextField(blank=True, help_text="JSON array of {label, url} objects")
    display_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title


class WAOHAnchor(models.Model):
    name = models.CharField(max_length=500)
    anchor = models.CharField(max_length=500, help_text="Anchor ID (e.g., 'immigration', 'fertility')")
    url = models.URLField(max_length=1000, help_text="Full URL to the WAOH anchor")
    category = models.CharField(max_length=200, blank=True, help_text="Category from WAOH index")
    stat_image = models.ForeignKey('StatImage', on_delete=models.SET_NULL, null=True, blank=True, help_text="Matched stat image by anchor")
    cached_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['anchor', 'url']

    def __str__(self):
        return f"{self.name} (#{self.anchor})"


class CertificationApplication(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    experience = models.TextField(blank=True)
    motivation = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.certification.title} - {self.first_name} {self.last_name}"
