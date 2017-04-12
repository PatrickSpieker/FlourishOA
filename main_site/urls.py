from main_site import views
from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^viz', views.VisualizationView.as_view(), name='viz'),
    url(r'^search', views.SearchView.as_view(), name='search'),
    url(r'^journal/(?P<issn>\d{4}-\d{3}[\dxX])/$', views.ResultView.as_view(), name='result'),
    url(r'^scatter', views.TemplateView.as_view(template_name='main_site/scatter.html')),
    url(r'^scatter-data', views.ScatterData.as_view())
]