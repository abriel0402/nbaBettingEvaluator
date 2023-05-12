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
    path("<str:stat>/<int:playerID>/", views.player, name="player-pa"),
    path("points+assists/", views.pa, name="pa"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-pr"),
    path("points+rebounds/", views.pr, name="pr"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-ra"),
    path("rebounds+assists/", views.ra, name="ra"),
    path("<str:stat>/<int:playerID>/", views.player, name="player-pra"),
    path("points+rebounds+assists/", views.pra, name="pra"),


]