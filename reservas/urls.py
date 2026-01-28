# reservas/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL para a página de reserva de um passeio específico
    # Ex: /reservas/passeio/praia-do-gunga/
    path('passeio/<slug:slug_da_praia>/', views.fazer_reserva_passeio, name='fazer_reserva_passeio'),

    # URL para a página de sucesso
    # Ex: /reservas/sucesso/
    path('sucesso/', views.reserva_sucesso, name='reserva_sucesso'),
    path('transfer/solicitar/', views.solicitar_transfer, name='solicitar_transfer'),
    path('falha/', views.reserva_falha, name='reserva_falha'),
    path('pendente/', views.reserva_pendente, name='reserva_pendente'),
    path('transfer/<slug:slug>/reservar/', views.fazer_reserva_transfer, name='fazer_reserva_transfer'),

    path('transfers/', views.lista_transfers, name='lista_transfers'),
    path('transfers/novo/', views.novo_transfer, name='novo_transfer'),
    path('transfers/editar/<int:transfer_id>/', views.editar_transfer, name='editar_transfer'),
    path('transfers/excluir/<int:transfer_id>/', views.excluir_transfer, name='excluir_transfer'),
]