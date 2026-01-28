# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL para a lista de posts (ex: /blog/)
    path('', views.lista_de_posts, name='lista_de_posts'),

    # URL para um post individual (ex: /blog/dicas-de-restaurantes/)
    path('<slug:slug>/', views.detalhe_do_post, name='detalhe_do_post'),
]