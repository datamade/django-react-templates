from django.shortcuts import render
from django.views.generic import TemplateView


class Home(TemplateView):
    title = 'Home'
    template_name = 'example_app/index.html'
    component = 'js/pages/index.js'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['props'] = {'user': 'jean'}  # Set React props here
        return context


def page_not_found(request, exception, template_name='example_app/404.html'):
    return render(request, template_name, status=404)


def server_error(request, template_name='example_app/500.html'):
    return render(request, template_name, status=500)
