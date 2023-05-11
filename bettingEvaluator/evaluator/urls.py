from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-pts"),
    path("points/", views.points, name="points"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-asts"),
    path("assists/", views.assists, name="assists"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-rebs"),
    path("rebounds/", views.rebounds, name="rebounds"),


]