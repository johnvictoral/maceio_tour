import json
import os
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail # <--- Importante para enviar e-mail
from django.template.loader import render_to_string # <--- Importante para ler o HTML
from django.utils.html import strip_tags # <--- Importante para segurança do e-mail

from .models import ImagemCarrossel, Praia, Transfer, Depoimento, Post, Reserva
from .forms import ClientePublicoForm, ReservaPublicaForm
from .mares_data import DADOS_MARES_2026

def home(request):
    imagens_carrossel = ImagemCarrossel.objects.filter(ativo=True)
    praias = Praia.objects.filter(ativo=True)
    transfers = Transfer.objects.all()
    depoimentos = Depoimento.objects.filter(ativo=True).order_by('-id')[:3]
    posts_recentes = Post.objects.filter(status='publicado').order_by('-data_publicacao')[:3]
    
    context = {
        'imagens_carrossel': imagens_carrossel,
        'praias': praias,
        'transfers': transfers,
        'depoimentos': depoimentos,
        'posts_recentes': posts_recentes,
    }
    
    return render(request, 'core/home.html', context)

def detalhe_praia(request, slug):
    praia = get_object_or_404(Praia, slug=slug)
    sugestoes = Praia.objects.exclude(slug=slug)[:3]
    context = {
        'praia': praia,
        'sugestoes': sugestoes,
    }
    return render(request, 'core/detalhe_praia.html', context)

def sobre_nos_view(request):
    return render(request, 'core/sobre_nos.html')

def contato_view(request):
    return render(request, 'core/contato.html')

def tabua_de_mares_view(request):
    meses_disponiveis = list(DADOS_MARES_2026.keys())
    mes_selecionado = request.GET.get('mes')
    
    if not mes_selecionado:
        mes_map_num = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        mes_atual_nome = mes_map_num.get(datetime.now().month)
        
        if mes_atual_nome in DADOS_MARES_2026:
            mes_selecionado = mes_atual_nome
        elif meses_disponiveis:
            mes_selecionado = meses_disponiveis[0]

    dados_do_mes = DADOS_MARES_2026.get(mes_selecionado, [])
    altura_anterior = None

    for dia_dados in dados_do_mes:
        mares_do_dia = dia_dados['mares']
        for mare_atual in mares_do_dia:
            if altura_anterior is not None:
                if mare_atual['altura'] > altura_anterior:
                    mare_atual['tendencia'] = 'subindo'
                elif mare_atual['altura'] < altura_anterior:
                    mare_atual['tendencia'] = 'descendo'
                else:
                    mare_atual['tendencia'] = 'estavel'
            altura_anterior = mare_atual['altura']

    if dados_do_mes and dados_do_mes[0]['mares']:
        primeira_mare = dados_do_mes[0]['mares'][0]
        if 'tendencia' not in primeira_mare:
            if len(dados_do_mes[0]['mares']) > 1:
                segunda_mare = dados_do_mes[0]['mares'][1]
                if primeira_mare['altura'] < segunda_mare['altura']:
                    primeira_mare['tendencia'] = 'subindo'
                else:
                    primeira_mare['tendencia'] = 'descendo'
            else:
                primeira_mare['tendencia'] = 'estavel'

    context = {
        'tabela_mares': dados_do_mes,
        'meses_disponiveis': meses_disponiveis,
        'mes_selecionado': mes_selecionado,
    }
    return render(request, 'core/tabua_de_mares.html', context)

def detalhe_transfer_view(request, slug):
    transfer = get_object_or_404(Transfer, slug=slug)
    context = {
        'transfer': transfer,
    }
    return render(request, 'core/detalhe_transfer.html', context)

def detalhe_post(request, slug):
    post = get_object_or_404(Post, slug=slug, status='publicado')
    outros_posts = Post.objects.filter(status='publicado').exclude(id=post.id).order_by('-data_publicacao')[:3]
    return render(request, 'core/detalhe_post.html', {
        'post': post, 
        'outros_posts': outros_posts
    })

def lista_de_posts(request):
    posts = Post.objects.filter(status='publicado').order_by('-data_publicacao')
    return render(request, 'core/lista_posts.html', {'posts': posts})

# --- FUNÇÃO DE ENVIAR E-MAIL (CORRIGIDA E FINAL) ---
def enviar_email_reserva(reserva, servico_nome):
    print(f"--- TENTANDO ENVIAR E-MAIL PARA {reserva.cliente.email} ---")
    
    try:
        assunto = f'Confirmação de Reserva #{reserva.codigo} - Vá com John'
        
        # Prepara os dados para o e-mail
        # AQUI ESTAVA O ERRO: O campo certo é data_agendamento!
        contexto = {
            'nome_cliente': reserva.cliente.nome,
            'codigo': reserva.codigo,
            'data_viagem': reserva.data_agendamento, # <--- CORRIGIDO AQUI (Era data_viagem)
            'servico': servico_nome,
            'valor': reserva.valor
        }

        # Tenta criar o HTML bonito
        try:
            html_content = render_to_string('core/emails/nova_reserva.html', contexto)
            text_content = strip_tags(html_content) # Cria versão texto
        except Exception as e_template:
            # Se der erro no HTML (agora não deve dar mais), manda texto simples
            print(f"ERRO DE TEMPLATE (Mas vamos enviar texto): {e_template}")
            html_content = f"<p>Olá {reserva.cliente.nome}, sua reserva <b>#{reserva.codigo}</b> foi recebida!</p>"
            text_content = f"Olá {reserva.cliente.nome}, sua reserva #{reserva.codigo} foi recebida!"

        # Envia de verdade
        send_mail(
            assunto,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [reserva.cliente.email],
            html_message=html_content,
            fail_silently=False
        )
        print("✅ E-MAIL ENVIADO COM SUCESSO!")
        return True

    except Exception as e:
        print(f"❌ ERRO FATAL AO ENVIAR E-MAIL: {e}")
        return False

def fazer_reserva_passeio(request, praia_id):
    praia = get_object_or_404(Praia, id=praia_id)
    sugestoes = Praia.objects.filter(ativo=True).exclude(id=praia.id)[:3]

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            # 1. Salva Cliente e Reserva
            cliente = cliente_form.save()
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            reserva.praia_destino = praia
            reserva.tipo = 'passeio'
            reserva.status = 'pendente'
            reserva.valor = praia.valor if praia.valor else 0.00
            reserva.save()
            
            # 2. Envia E-mail (Sem esconder o erro)
            sucesso_email = enviar_email_reserva(reserva, praia.nome)
            
            if sucesso_email:
                messages.success(request, f"Reserva confirmada! O voucher foi enviado para {cliente.email}.")
            else:
                messages.warning(request, f"Reserva feita, mas houve um erro ao enviar o e-mail. Entre em contato conosco.")

            return redirect('reserva_confirmada') # Redireciona para evitar reenvio de formulário
            
    else:
        cliente_form = ClientePublicoForm()
        reserva_form = ReservaPublicaForm()

    return render(request, 'core/fazer_reserva.html', {
        'praia': praia,
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
        'sugestoes': sugestoes
    })

def fazer_reserva_transfer(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    sugestoes = Transfer.objects.filter().exclude(id=transfer.id)[:3]

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            # 1. Salva Cliente
            cliente = cliente_form.save()
            
            # 2. Salva Reserva
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            reserva.tipo = 'transfer'
            reserva.local_chegada = transfer.titulo
            reserva.status = 'pendente'
            reserva.valor = transfer.valor
            reserva.save()
            
            # 3. Envia E-mail (Com verificação de sucesso)
            sucesso_email = enviar_email_reserva(reserva, f"Transfer: {transfer.titulo}")
            
            if sucesso_email:
                messages.success(request, f"Solicitação de Transfer '{transfer.titulo}' enviada! Verifique seu e-mail.")
            else:
                messages.warning(request, f"Solicitação recebida, mas houve um erro ao enviar o e-mail de confirmação.")

            return redirect('reserva_confirmada')
    else:
        cliente_form = ClientePublicoForm()
        reserva_form = ReservaPublicaForm()

    return render(request, 'core/fazer_reserva_transfer.html', {
        'transfer': transfer,
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
        'sugestoes': sugestoes
    })

def reserva_confirmada(request):
    return render(request, 'core/confirmacao.html')

def consultar_reserva(request):
    reserva = None
    erro = None
    
    if request.method == 'POST':
        codigo_busca = request.POST.get('codigo', '').strip().upper().replace('#', '')
        sobrenome_busca = request.POST.get('sobrenome', '').strip()
        
        if codigo_busca and sobrenome_busca:
            try:
                reserva = Reserva.objects.get(
                    codigo=codigo_busca, 
                    cliente__sobrenome__iexact=sobrenome_busca
                )
            except Reserva.DoesNotExist:
                erro = "Reserva não encontrada. Verifique o código e o sobrenome."
        else:
            erro = "Preencha todos os campos."

    return render(request, 'core/minha_reserva.html', {'reserva': reserva, 'erro': erro})