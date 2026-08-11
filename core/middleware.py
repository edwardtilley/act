class FrameAncestorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = "frame-ancestors 'self' http://localhost:5000 http://127.0.0.1:5000 http://ubuntu:5000"
        return response
