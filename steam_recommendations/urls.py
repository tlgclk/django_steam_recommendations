from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('games/', views.game_list, name='game_list'),
    path('test/', views.test, name='test'),
    path('login/', views.login_view, name='login'),
    path('my_games/', views.my_games_view, name='my_games'),
    path('my_games/', views.my_games_view, name='my_games'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('logout/', views.logout_view, name='logout'),
    path('cf_recommendations/', views.cf_recommendations_view, name='cf_recommendations'),
    path('cf_similarities/', views.cf_similarities_view, name='cf_similarities'),
    path('cb_recommendations/', views.cb_recommendations_view, name='cb_recommendations'),
]
