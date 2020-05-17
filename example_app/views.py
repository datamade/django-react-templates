from django.shortcuts import render
from django.views.generic import TemplateView


class Client(TemplateView):
    """
    A view demonstrating a purely client-side React integration.
    """
    title = 'Client'
    template_name = 'example_app/client.html'
    component = 'js/pages/client.js'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['props'] = {'user': 'jean'}  # Set React props here
        return context


class Server(TemplateView):
    """
    A view demonstrating a server-side rendered React integration.
    """
    title = 'Server'
    template_name = 'example_app/App.js'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['name'] = 'jean'
        return context


def page_not_found(request, exception, template_name='example_app/404.html'):
    return render(request, template_name, status=404)


def server_error(request, template_name='example_app/500.html'):
    return render(request, template_name, status=500)
