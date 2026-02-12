# dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.painel, name='painel'), # A URL /dashboard/ aponta para a view 'painel'
    path('configuracoes/banner/', views.gerenciar_banner, name='gerenciar_banner'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('reserva/<int:reserva_id>/', views.detalhe_reserva, name='detalhe_reserva'),
    path('reserva/<int:reserva_id>/recibo-pdf/', views.gerar_recibo_pdf, name='gerar_recibo_pdf'),
    path('recibo-manual/', views.gerar_recibo_manual, name='gerar_recibo_manual'),
    path('reserva/<int:reserva_id>/excluir/', views.excluir_reserva, name='excluir_reserva'),
    path('calendario/', views.calendario_view, name='calendario_view'),
    path('calendario/api/reservas/', views.calendario_api, name='calendario_api'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/<int:cliente_id>/excluir/', views.excluir_cliente, name='excluir_cliente'),
    path('parceiros/', views.lista_parceiros, name='lista_parceiros'),
    path('parceiros/<int:guia_id>/excluir/', views.excluir_parceiro, name='excluir_parceiro'),
    path('reserva/<int:reserva_id>/editar/', views.editar_reserva, name='editar_reserva'),
    path('nova-reserva/', views.nova_reserva_manual, name='nova_reserva_manual'),
    # Praias
    path('praias/', views.lista_praias, name='lista_praias'),
    path('praias/nova/', views.nova_praia, name='nova_praia'),
    path('praias/editar/<int:praia_id>/', views.editar_praia, name='editar_praia'),
    path('praias/excluir/<int:praia_id>/', views.excluir_praia, name='excluir_praia'),

    # Clientes (Adicione as de cadastro/edição)
    path('clientes/novo/', views.novo_cliente, name='novo_cliente'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    # dashboard/urls.py
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('voucher/<int:reserva_id>/', views.gerar_voucher, name='gerar_voucher'),
    path('depoimentos/', views.lista_depoimentos, name='lista_depoimentos'),
path('depoimentos/novo/', views.novo_depoimento, name='novo_depoimento'),
path('depoimentos/excluir/<int:depoimento_id>/', views.excluir_depoimento, name='excluir_depoimento'),
    # Blog
    path('blog/', views.lista_posts, name='lista_posts'),
    path('blog/novo/', views.novo_post, name='novo_post'),
    path('blog/editar/<int:post_id>/', views.editar_post, name='editar_post'),
    path('blog/excluir/<int:post_id>/', views.excluir_post, name='excluir_post'),

    # Banners / Carrossel
    path('carrossel/', views.gerenciar_carrossel, name='gerenciar_carrossel'),
    path('carrossel/novo/', views.novo_carrossel, name='novo_carrossel'),
    path('carrossel/editar/<int:item_id>/', views.editar_carrossel, name='editar_carrossel'),
    path('carrossel/excluir/<int:item_id>/', views.excluir_carrossel, name='excluir_carrossel'),
    # --- ADICIONE ISTO AQUI: TRANSFERS ---
    path('transfers/', views.lista_transfers, name='lista_transfers'),
    path('transfers/novo/', views.novo_transfer, name='novo_transfer'),
    path('transfers/editar/<int:transfer_id>/', views.editar_transfer, name='editar_transfer'),
    path('transfers/excluir/<int:transfer_id>/', views.excluir_transfer, name='excluir_transfer'),
    path('reservas/', views.lista_reservas, name='lista_reservas'),

    # Rota de Parceiros
    path('parceiros/', views.lista_parceiros, name='lista_parceiros'),
    path('parceiros/excluir/<int:guia_id>/', views.excluir_parceiro, name='excluir_parceiro'),

    # --- AQUI ESTÁ A CORREÇÃO DO ERRO ---
    # O 'name' deve ser igual ao que está no menu lateral (recibo_manual)
    path('financeiro/recibo/', views.gerar_recibo_manual, name='recibo_manual'),
    
    # Rota para o recibo da reserva (Automático)
    path('reservas/recibo/<int:reserva_id>/', views.gerar_recibo_pdf, name='gerar_recibo_pdf'),
    # Rota para o Recibo Financeiro (Separado do Voucher)
path('financeiro/comprovante/<int:reserva_id>/', views.gerar_recibo_financeiro, name='gerar_recibo_financeiro'),

path('bloqueios/', views.gerenciar_bloqueios, name='gerenciar_bloqueios'),
path('bloqueios/excluir/<int:bloqueio_id>/', views.excluir_bloqueio, name='excluir_bloqueio'),
]