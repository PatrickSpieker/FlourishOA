from main_site import views
from django.conf.urls import url

urlpatterns = [
    url(r'^viz', views.VisualizationView.as_view(), name='viz'),
    url(r'^search', views.SearchView.as_view(), name='search'),
    url(r'^journal/(?P<issn>[0-9]+)$', views.ResultView.as_view(), name='result'),
    url(r'', views.IndexView.as_view(), name='index'),
]