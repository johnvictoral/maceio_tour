from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('praia/<slug:slug>/', views.detalhe_praia, name='detalhe_praia'),
    path('sobre-nos/', views.sobre_nos_view, name='sobre_nos'),
    path('contato/', views.contato_view, name='contato'),
    path('tabua-de-mares/', views.tabua_de_mares_view, name='tabua_de_mares'),
    path('transfer/<slug:slug>/', views.detalhe_transfer_view, name='detalhe_transfer'),
    
    path('blog/', views.lista_de_posts, name='lista_de_posts'),
    
    path('blog/<slug:slug>/', views.detalhe_post, name='detalhe_do_post'),
    path('reservar/<int:praia_id>/', views.fazer_reserva_passeio, name='fazer_reserva_passeio'),
    # ROTA NOVA (Adicione esta linha):
    path('transfer/reservar/<int:transfer_id>/', views.fazer_reserva_transfer, name='fazer_reserva_transfer'),
    path('confirmacao/', views.reserva_confirmada, name='reserva_confirmada'),
]