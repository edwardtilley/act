from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import Riding, JoinApplication, Certification, CertificationApplication, StatImage, WAOHAnchor


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
    return render(request, 'pages/stateditor.html', {'stats': stats, 'segment': 'stats', 'saved': request.GET.get('saved')})


@login_required
def stat_create(request):
    if request.method == 'POST':
        StatImage.objects.create(
            title=request.POST.get('title', ''),
            image_filename=request.POST.get('image_filename', ''),
            description=request.POST.get('description', ''),
            keywords=request.POST.get('keywords', ''),
            links_json=request.POST.get('links_json', ''),
            active='active' in request.POST,
        )
    return redirect('/stateditor')


@login_required
def stat_update(request, stat_id):
    stat = get_object_or_404(StatImage, pk=stat_id)
    if request.method == 'POST':
        stat.title = request.POST.get('title', stat.title)
        stat.image_filename = request.POST.get('image_filename', stat.image_filename)
        stat.description = request.POST.get('description', stat.description)
        stat.keywords = request.POST.get('keywords', stat.keywords)
        stat.links_json = request.POST.get('links_json', stat.links_json)
        stat.active = 'active' in request.POST
        stat.save()
        return redirect('/stateditor?saved=%s' % stat_id)
    return redirect('/stateditor')


@login_required
def stat_delete(request, stat_id):
    stat = get_object_or_404(StatImage, pk=stat_id)
    if request.method == 'POST':
        stat.delete()
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
