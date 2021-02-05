from django.shortcuts import render

from django.views.generic.base import View


class StripeWixProxyView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'stripeWixProxy.html')

    # def reverse(*args, **kwargs):
    #     get = kwargs.pop('get', {})
    #     url = reverse(*args, **kwargs)
    #     if get:
    #         url += '?' + urlencode(get)
    #     return url
