import io
import logging
import os
import shutil
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.db import transaction
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.text import get_valid_filename
from PIL import Image

from .models import Riding, JoinApplication, Certification, CertificationApplication, StatImage, WAOHAnchor


STAT_IMAGE_DIR = Path(settings.BASE_DIR) / 'static' / 'assets' / 'img'
STAT_IMAGE_MAX_BYTES = 10 * 1024 * 1024
STAT_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
STATS_FIXTURE = Path(settings.BASE_DIR) / 'stats.json'
PRODUCTION_HOSTS = {'actcanadian.com', 'www.actcanadian.com'}

logger = logging.getLogger(__name__)


def _is_production_request(request):
    host = request.get_host().split(':')[0].lower()
    return (
        not settings.DEBUG
        or host in PRODUCTION_HOSTS
        or host.endswith('.up.railway.app')
    )


def _refresh_stats_fixture(request):
    """Refresh stats.json after a dev edit so deployment order/image changes
    are captured in the repository fixture.

    Production is deliberately skipped: the container is rebuilt on deploy and
    its filesystem is ephemeral, so prod edits are moved back with the export
    bundle instead.
    """
    if _is_production_request(request):
        return False
    try:
        output = io.StringIO()
        call_command(
            'dumpdata', 'party_pages.StatImage', 'party_pages.WAOHAnchor',
            indent=2, stdout=output,
        )
        STATS_FIXTURE.write_text(output.getvalue(), encoding='utf-8')
        return True
    except Exception:
        logger.exception('Could not refresh stats.json fixture')
        return False


def _unique_stat_image_name(filename):
    base, ext = os.path.splitext(filename)
    candidate = filename
    n = 1
    while (STAT_IMAGE_DIR / candidate).exists():
        candidate = f'{base}-{n}{ext}'
        n += 1
    return candidate


def _mirror_stat_image(filename):
    """Mirror a saved image into STATIC_ROOT so WhiteNoise serves it in prod."""
    static_root = getattr(settings, 'STATIC_ROOT', None)
    if not static_root:
        return
    src = STAT_IMAGE_DIR / filename
    dest_dir = Path(static_root) / 'assets' / 'img'
    try:
        if src.exists() and dest_dir.resolve() != STAT_IMAGE_DIR.resolve():
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest_dir / filename)
    except OSError:
        pass


def _store_stat_image(upload, preferred_name=''):
    """Save an uploaded stat image into static/assets/img/ and return its
    filename, or None when the upload is missing/not an allowed image.

    When preferred_name is given, the upload is saved under that name (with
    the real image format's extension). In production WhiteNoise serves
    STATIC_ROOT, so the file is mirrored there too; note that the Railway
    filesystem is ephemeral and rebuilds on deploy, so uploads must be
    committed (static file + stats.json fixture) to last.
    """
    if not upload or upload.size > STAT_IMAGE_MAX_BYTES:
        return None
    upload_ext = os.path.splitext(upload.name)[1].lower()
    if upload_ext not in STAT_IMAGE_EXTS:
        return None
    try:
        Image.open(upload).verify()
    except Exception:
        return None
    upload.seek(0)

    STAT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    preferred = os.path.basename(preferred_name or '').strip()
    if preferred:
        stem = os.path.splitext(preferred)[0]
        desired = (get_valid_filename(stem) or os.path.splitext(upload.name)[0]) + upload_ext
    else:
        desired = get_valid_filename(upload.name)
    filename = _unique_stat_image_name(desired)
    storage = FileSystemStorage(location=str(STAT_IMAGE_DIR))
    saved = storage.save(filename, upload)
    _mirror_stat_image(saved)
    return saved


def _copy_stat_image(old_name, new_name):
    """Copy an existing stat image to a new filename.

    Used when the Image Filename field is edited without uploading a new file,
    so the typed name is actually applied instead of pointing at nothing.
    """
    desired = get_valid_filename(os.path.basename(new_name or ''))
    if not desired:
        return old_name
    if desired == old_name:
        return old_name
    src = STAT_IMAGE_DIR / old_name
    if not src.exists():
        return desired
    filename = _unique_stat_image_name(desired)
    try:
        shutil.copyfile(src, STAT_IMAGE_DIR / filename)
    except OSError:
        return old_name
    _mirror_stat_image(filename)
    return filename


def index(request):
    return render(request, 'pages/index.html')


def index1(request):
    return render(request, 'pages/index1.html')


def index2(request):
    return render(request, 'pages/index2.html')


def index3(request):
    return render(request, 'pages/index3.html')


def map_view(request):
    ridings = Riding.objects.all()
    context = {
        'ridings': ridings,
        'provinces': Riding.objects.values_list('province', flat=True).distinct().order_by('province'),
    }
    return render(request, 'pages/map.html', context)


def map_data(request):
    ridings = Riding.objects.all().values(
        'id', 'province', 'region', 'riding_name', 'mp_name', 'mp_party',
        'mpp_name', 'mpp_party', 'latitude', 'longitude',
        'candidate_name', 'candidate_url'
    )
    return JsonResponse(list(ridings), safe=False)


def candidates(request):
    ridings = Riding.objects.all()
    context = {
        'ridings': ridings,
        'provinces': Riding.objects.values_list('province', flat=True).distinct().order_by('province'),
    }
    return render(request, 'pages/candidates.html', context)


def riding_office(request, slug):
    from apps.authentication.models import UserProfile
    riding = get_object_or_404(Riding, candidate_url=slug)
    certification = riding.candidate_certification or ''
    if not certification and riding.candidate_name:
        full_name = ' '.join(str(riding.candidate_name).strip().lower().split())
        for profile in UserProfile.objects.select_related('user'):
            profile_name = ' '.join(
                f"{profile.user.first_name} {profile.user.last_name}".strip().lower().split()
            )
            if profile_name == full_name:
                certification = profile.certification or ''
                break
    badge = None
    if certification == 'graduate':
        badge = {'image': 'badge-civic-scientist.svg', 'tooltip': 'Professional Civic Scientist'}
    elif certification == 'trainee':
        badge = {'image': 'badge-civic-scientist-trainee.svg', 'tooltip': 'Trainee'}
    context = {
        'riding': riding,
        'badge': badge,
        'certification': certification,
    }
    return render(request, 'pages/riding_office.html', context)


def policies(request):
    return render(request, 'pages/policies.html')


def _parse_date(value):
    if not value:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _apply_candidate_form(riding, request):
    from django.utils.text import slugify
    riding.candidate_name = request.POST.get('candidate_name', '').strip() or None
    riding.candidate_bio = request.POST.get('candidate_bio', '')
    riding.candidate_certification = request.POST.get('candidate_certification', '')
    riding.candidate_status = request.POST.get('candidate_status', '')
    riding.candidate_accepted_at = _parse_date(request.POST.get('candidate_accepted_at'))
    riding.candidate_accepted_by = request.POST.get('candidate_accepted_by', '').strip()
    riding.candidate_elected = 'candidate_elected' in request.POST
    if request.FILES.get('candidate_photo'):
        riding.candidate_photo = request.FILES['candidate_photo']
    if riding.candidate_name and not riding.candidate_url:
        riding.candidate_url = slugify(f"{riding.candidate_name}-{riding.riding_name}")
    riding.save()


@login_required
def admin_candidates(request):
    ridings = (Riding.objects
               .exclude(candidate_name__isnull=True)
               .exclude(candidate_name='')
               .order_by('province', 'riding_name'))
    open_ridings = (Riding.objects
                    .filter(candidate_name__isnull=True) | Riding.objects.filter(candidate_name=''))
    context = {
        'segment': 'admin_candidates',
        'ridings': ridings,
        'open_ridings': open_ridings.order_by('province', 'riding_name'),
        'status_choices': Riding.CANDIDATE_STATUS_CHOICES,
        'saved': request.GET.get('saved'),
    }
    return render(request, 'pages/admin_candidates.html', context)


@login_required
def admin_candidate_create(request):
    if request.method == 'POST':
        riding = get_object_or_404(Riding, pk=request.POST.get('riding_id'))
        _apply_candidate_form(riding, request)
        return redirect('/admin-candidates?saved=new')
    return redirect('/admin-candidates')


@login_required
def admin_candidate_update(request, riding_id):
    riding = get_object_or_404(Riding, pk=riding_id)
    if request.method == 'POST':
        _apply_candidate_form(riding, request)
        return redirect('/admin-candidates?saved=%s' % riding_id)
    return redirect('/admin-candidates')


@login_required
def admin_candidate_status(request, riding_id):
    riding = get_object_or_404(Riding, pk=riding_id)
    if request.method == 'POST':
        status = request.POST.get('candidate_status', '')
        if status in dict(Riding.CANDIDATE_STATUS_CHOICES):
            riding.candidate_status = status
            riding.save(update_fields=['candidate_status'])
    return redirect('/admin-candidates')


@login_required
def admin_candidate_delete(request, riding_id):
    riding = get_object_or_404(Riding, pk=riding_id)
    if request.method == 'POST':
        riding.candidate_name = None
        riding.candidate_photo = None
        riding.candidate_bio = ''
        riding.candidate_certification = ''
        riding.candidate_status = ''
        riding.candidate_accepted_at = None
        riding.candidate_accepted_by = ''
        riding.candidate_elected = False
        riding.save()
    return redirect('/admin-candidates')


def candidate_join(request):
    if request.method == 'POST':
        JoinApplication.objects.create(
            application_type='candidate',
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            province=request.POST.get('province', ''),
            postal_code=request.POST.get('postal_code', ''),
            message=request.POST.get('message', ''),
        )
        return redirect('/candidate-join?submitted=1')
    return render(request, 'pages/candidate_join.html')


def member_join(request):
    if request.method == 'POST':
        JoinApplication.objects.create(
            application_type='member',
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            province=request.POST.get('province', ''),
            postal_code=request.POST.get('postal_code', ''),
            message=request.POST.get('message', ''),
        )
        return redirect('/member-join?submitted=1')
    return render(request, 'pages/member_join.html')


def certifications(request):
    certs = Certification.objects.filter(active=True)
    if request.method == 'POST':
        cert_id = request.POST.get('certification_id')
        cert = Certification.objects.get(id=cert_id)
        CertificationApplication.objects.create(
            certification=cert,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            experience=request.POST.get('experience', ''),
            motivation=request.POST.get('motivation', ''),
        )
        return redirect('/certifications?submitted=1')
    context = {'certifications': certs}
    return render(request, 'pages/certifications.html', context)


@login_required
def dashboard(request):
    from apps.shop.services import hub_gateway_config
    cfg = hub_gateway_config()
    gateway_mode = 'hub' if (cfg['url'] and cfg['api_key']) else 'simulated'
    return render(request, 'pages/dashboard.html', {
        'segment': 'dashboard',
        'gateway_mode': gateway_mode,
        'gateway_mode_display': 'LIVE HUB' if gateway_mode == 'hub' else 'SIMULATED',
        'gateway_url': cfg['url'],
    })


def stats_slideshow(request):
    stats = StatImage.objects.filter(active=True)
    waoh_anchors = WAOHAnchor.objects.all()
    return render(request, 'pages/stats.html', {'stats': stats, 'waoh_anchors': waoh_anchors})


@login_required
def stat_editor(request):
    stats = StatImage.objects.all()
    return render(request, 'pages/stateditor.html', {
        'stats': stats,
        'segment': 'stats',
        'saved': request.GET.get('saved'),
        'is_production': _is_production_request(request),
    })


@login_required
def stat_export(request):
    """Download stats.json plus every referenced image.

    Production rebuilds the container on each deploy, so uploads/renames made
    there are lost unless they are brought back into the repository. This
    bundle is the bridge: unzip it over the repo, commit, and push.
    """
    fixture = io.StringIO()
    call_command(
        'dumpdata', 'party_pages.StatImage', 'party_pages.WAOHAnchor',
        indent=2, stdout=fixture,
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('stats.json', fixture.getvalue())
        bundle.writestr('README.txt', (
            f'Stats export — {timezone.now():%Y-%m-%d %H:%M} UTC\n\n'
            "1. Copy static/assets/img/* into the repo's static/assets/img/.\n"
            "2. Replace the repo's stats.json with the one in this archive.\n"
            '3. Commit and push so the next deploy seeds these changes.\n'
        ))
        for stat in StatImage.objects.exclude(image_filename=''):
            path = STAT_IMAGE_DIR / stat.image_filename
            if path.exists():
                bundle.write(path, f'static/assets/img/{stat.image_filename}')

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="stats-export.zip"'
    return response


@login_required
def stat_create(request):
    if request.method == 'POST':
        filename = os.path.basename(request.POST.get('image_filename', '').strip())
        upload = request.FILES.get('stat_image')
        if upload:
            stored = _store_stat_image(upload, filename)
            if not stored:
                messages.error(request, 'Upload failed — choose a JPEG, PNG, WebP or GIF image under 10 MB.')
                return redirect('/stateditor')
            filename = stored
        StatImage.objects.create(
            title=request.POST.get('title', ''),
            image_filename=filename,
            description=request.POST.get('description', ''),
            keywords=request.POST.get('keywords', ''),
            links_json=request.POST.get('links_json', ''),
            active='active' in request.POST,
            display_order=(StatImage.objects.aggregate(Max('display_order'))['display_order__max'] or 0) + 1,
        )
        _refresh_stats_fixture(request)
    return redirect('/stateditor')


@login_required
def stat_move(request, stat_id, direction):
    """Move a stat up/down the shared display order used by /stats."""
    if request.method != 'POST' or direction not in ('up', 'down'):
        return redirect('/stateditor')
    stat = get_object_or_404(StatImage, pk=stat_id)
    rows = list(StatImage.objects.order_by('display_order', 'id'))
    idx = next((i for i, row in enumerate(rows) if row.pk == stat.pk), None)
    if idx is None:
        return redirect('/stateditor')
    target = idx - 1 if direction == 'up' else idx + 1
    if 0 <= target < len(rows):
        rows[idx], rows[target] = rows[target], rows[idx]
        with transaction.atomic():
            for pos, row in enumerate(rows):
                StatImage.objects.filter(pk=row.pk).update(display_order=pos)
        _refresh_stats_fixture(request)
    return redirect('/stateditor')


@login_required
def stat_update(request, stat_id):
    stat = get_object_or_404(StatImage, pk=stat_id)
    if request.method == 'POST':
        filename = os.path.basename(
            request.POST.get('image_filename', stat.image_filename).strip()
        )
        upload = request.FILES.get('stat_image')
        if upload:
            stored = _store_stat_image(upload, filename or stat.image_filename)
            if not stored:
                messages.error(request, 'Upload failed — choose a JPEG, PNG, WebP or GIF image under 10 MB.')
                return redirect('/stateditor')
            filename = stored
        elif filename and filename != stat.image_filename:
            filename = _copy_stat_image(stat.image_filename, filename)
        stat.title = request.POST.get('title', stat.title)
        stat.image_filename = filename
        stat.description = request.POST.get('description', stat.description)
        stat.keywords = request.POST.get('keywords', stat.keywords)
        stat.links_json = request.POST.get('links_json', stat.links_json)
        stat.active = 'active' in request.POST
        stat.save()
        _refresh_stats_fixture(request)
        return redirect('/stateditor?saved=%s' % stat_id)
    return redirect('/stateditor')


@login_required
def stat_delete(request, stat_id):
    stat = get_object_or_404(StatImage, pk=stat_id)
    if request.method == 'POST':
        stat.delete()
        rows = list(StatImage.objects.order_by('display_order', 'id'))
        with transaction.atomic():
            for pos, row in enumerate(rows):
                StatImage.objects.filter(pk=row.pk).update(display_order=pos)
        _refresh_stats_fixture(request)
    return redirect('/stateditor')


@login_required
def profile(request):
    from apps.authentication.models import UserProfile
    saved = request.GET.get('saved') or request.GET.get('pwd')
    pw_form = PasswordChangeForm(request.user)
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'change_password' in request.POST:
            pw_form = PasswordChangeForm(request.user, request.POST)
            if pw_form.is_valid():
                pw_form.save()
                update_session_auth_hash(request, request.user)
                return redirect('/profile?pwd=1')
        else:
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            profile_obj.role = request.POST.get('role', 'member')
            profile_obj.certification = request.POST.get('certification', '')
            if request.FILES.get('profile_photo'):
                profile_obj.photo = request.FILES['profile_photo']
            elif 'remove_photo' in request.POST:
                profile_obj.photo.delete(save=False)
                profile_obj.photo = None
            profile_obj.save()
            return redirect('/profile?saved=1')
    return render(request, 'pages/profile.html', {
        'segment': 'profile',
        'pw_form': pw_form,
        'saved': saved,
        'profile_obj': profile_obj,
    })


def pricing(request):
    from apps.shop.models import Product
    products = {p.name: p.pk for p in Product.objects.filter(active=True)}
    return render(request, 'pages/pricing.html', {
        'segment': 'pricing',
        'certifications_id': products.get('Certification Training'),
        'mp_id': products.get('Federal Member of Parliament'),
        'mpp_id': products.get('Provincial Member of Parliament'),
    })
