from django.utils import translation

class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get('lang') or request.session.get('lang') or 'en'
        if lang not in ('en', 'fr'):
            lang = 'en'
        if lang != translation.get_language():
            translation.activate(lang)
            request.session['lang'] = lang
        response = self.get_response(request)
        return response
