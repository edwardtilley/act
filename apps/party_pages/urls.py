from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index1', views.index1, name='index1'),
    path('index2', views.index2, name='index2'),
    path('index3', views.index3, name='index3'),
    path('map', views.map_view, name='map'),
    path('map/data', views.map_data, name='map_data'),
    path('candidates', views.candidates, name='candidates'),
    path('candidates/<slug:slug>/', views.riding_office, name='riding_office'),
    path('policies', views.policies, name='policies'),
    path('candidate-join', views.candidate_join, name='candidate_join'),
    path('member-join', views.member_join, name='member_join'),
    path('certifications', views.certifications, name='certifications'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('profile', views.profile, name='profile'),
    path('pricing', views.pricing, name='pricing'),
    path('stats', views.stats_slideshow, name='stats'),
    path('stateditor', views.stat_editor, name='stat_editor'),
    path('stateditor/create/', views.stat_create),
    path('stateditor/update/<int:stat_id>/', views.stat_update),
    path('stateditor/delete/<int:stat_id>/', views.stat_delete),
]
