import json
import os
import io # <--- Importante para o PDF
from datetime import datetime
from django.db.models import Q

from django.core.serializers.json import DjangoJSONEncoder
from core.models import Bloqueio # Importe o Bloqueio

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives # <--- Importante para anexo
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# --- Importações para Gerar PDF ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .forms import CadastroParceiroForm # Importe o form que criamos

# Adicionei 'Guia' nas importações
from .models import ImagemCarrossel, Praia, Transfer, Depoimento, Post, Reserva, Guia
from .forms import ClientePublicoForm, ReservaPublicaForm
from .mares_data import DADOS_MARES_2026

# =======================================================
# 1. FUNÇÕES AUXILIARES (PDF E EMAIL DE CONFIRMAÇÃO)
# =======================================================

def gerar_voucher_pdf(reserva):
    """Gera o PDF do Voucher na memória"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- CABEÇALHO ---
    p.setFillColor(colors.darkgreen)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, 800, "VÁ COM JOHN TURISMO")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, "Maceió - Alagoas | CNPJ: JVC Turismo")
    p.drawString(50, 765, "WhatsApp: (82) 99932-5548")
    p.line(50, 750, 550, 750)
    
    # --- TÍTULO ---
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, 720, f"VOUCHER DE CONFIRMAÇÃO #{reserva.codigo}")
    
    # --- DADOS ---
    y = 680
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "DADOS DO CLIENTE")
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Nome: {reserva.cliente.nome} {reserva.cliente.sobrenome}")
    p.drawString(50, y-20, f"Email: {reserva.cliente.email}")
    p.drawString(50, y-40, f"Telefone: {reserva.cliente.telefone}")
    
    y -= 80
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "DETALHES DO SERVIÇO")
    y -= 25
    p.setFont("Helvetica", 12)
    
    servico = "Serviço Personalizado"
    if reserva.praia_destino:
        servico = f"Passeio: {reserva.praia_destino.nome}"
    elif reserva.tipo == 'transfer':
        servico = f"Transfer: {reserva.local_chegada or 'Ida/Volta'}"
        
    p.drawString(50, y, f"Serviço: {servico}")
    
    data_formatada = reserva.data_agendamento.strftime('%d/%m/%Y às %H:%M')
    p.drawString(50, y-20, f"Data: {data_formatada}")
    p.drawString(50, y-40, f"Passageiros: {reserva.numero_passageiros}")
    
    if reserva.local_partida:
        p.drawString(50, y-60, f"Local de Saída: {reserva.local_partida}")

    # --- GUIA ---
    if reserva.guia:
        y -= 110
        p.setFillColor(colors.aliceblue)
        p.rect(40, y-80, 515, 95, fill=1, stroke=0)
        p.setFillColor(colors.darkblue)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "SEU MOTORISTA / GUIA")
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y-25, f"Nome: {reserva.guia.nome}")
        p.setFont("Helvetica", 12)
        p.drawString(50, y-45, f"Veículo: {reserva.guia.modelo_carro} - {reserva.guia.cor_carro}")
        p.drawString(300, y-45, f"Placa: {reserva.guia.placa_carro}")
        p.drawString(50, y-65, f"Telefone: {reserva.guia.telefone}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def disparar_email_confirmacao(request, reserva):
    """Envia o e-mail de confirmação com o PDF em anexo"""
    try:
        print(f"--- PREPARANDO E-MAIL COM PDF PARA {reserva.cliente.email} ---")
        servico_nome = reserva.praia_destino.nome if reserva.praia_destino else (reserva.local_chegada or "Transfer")
        
        # HTML do corpo do e-mail
        # Tenta renderizar o HTML, se não existir, usa texto simples
        try:
            html_content = render_to_string('core/emails/reserva_confirmada.html', {
                'nome_cliente': reserva.cliente.nome,
                'codigo': reserva.codigo,
                'data_viagem': reserva.data_agendamento,
                'servico': servico_nome,
                'guia': reserva.guia,
            })
        except:
            html_content = f"<p>Sua reserva #{reserva.codigo} foi confirmada!</p>"

        text_content = strip_tags(html_content)
        
        # Gera o PDF
        pdf_buffer = gerar_voucher_pdf(reserva)
        filename = f"Voucher_{reserva.codigo}.pdf"

        # Monta o e-mail
        email = EmailMultiAlternatives(
            subject=f'Reserva CONFIRMADA + Voucher #{reserva.codigo}',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[reserva.cliente.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
        
        email.send()
        messages.success(request, f"✅ E-mail com Voucher PDF enviado para {reserva.cliente.nome}!")
        return True
    except Exception as e:
        print(f"ERRO AO ENVIAR EMAIL: {e}")
        messages.warning(request, f"Reserva salva, mas erro ao enviar e-mail: {e}")
        return False

# =======================================================
# 2. VIEWS DO DASHBOARD (NOVA LÓGICA)
# =======================================================

def detalhe_reserva(request, reserva_id):
    """View para gerenciar a reserva no Dashboard"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    guias = Guia.objects.filter(ativo=True)

    if request.method == 'POST':
        
        # --- CASO 1: Alteração de Status (Botões Confirmar/Cancelar) ---
        if 'status' in request.POST:
            novo_status = request.POST.get('status')
            reserva.status = novo_status
            reserva.save()
            
            # SE CONFIRMOU, ENVIA O EMAIL
            if novo_status == 'confirmado':
                disparar_email_confirmacao(request, reserva)
            else:
                messages.success(request, f"Status atualizado para {reserva.get_status_display()}!")
            
            return redirect('detalhe_reserva', reserva_id=reserva.id)

        # --- CASO 2: Atribuir Guia (Botão Salvar Guia) ---
        if 'guia' in request.POST:
            guia_id = request.POST.get('guia')
            if guia_id:
                guia_escolhido = get_object_or_404(Guia, id=guia_id)
                reserva.guia = guia_escolhido
                reserva.save()
                messages.success(request, f"Guia {guia_escolhido.nome} atribuído com sucesso!")
                
                # Se a reserva JÁ ESTAVA confirmada, reenvia o voucher atualizado com o guia
                if reserva.status == 'confirmado':
                    disparar_email_confirmacao(request, reserva)
            
            return redirect('detalhe_reserva', reserva_id=reserva.id)

    return render(request, 'core/detalhe_reserva.html', {
        'reserva': reserva,
        'guias': guias
    })

# =======================================================
# 3. VIEWS DO SITE (EXISTENTES)
# =======================================================

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

# --- FUNÇÃO DE ENVIAR E-MAIL INICIAL (CLIENTE SOLICITOU) ---
def enviar_email_reserva(reserva, servico_nome):
    print(f"--- TENTANDO ENVIAR E-MAIL PARA {reserva.cliente.email} ---")
    
    try:
        assunto = f'Confirmação de Reserva #{reserva.codigo} - Vá com John'
        
        contexto = {
            'nome_cliente': reserva.cliente.nome,
            'codigo': reserva.codigo,
            'data_viagem': reserva.data_agendamento,
            'servico': servico_nome,
            'valor': reserva.valor
        }

        try:
            html_content = render_to_string('core/emails/nova_reserva.html', contexto)
            text_content = strip_tags(html_content)
        except Exception as e_template:
            print(f"ERRO DE TEMPLATE (Mas vamos enviar texto): {e_template}")
            html_content = f"<p>Olá {reserva.cliente.nome}, sua reserva <b>#{reserva.codigo}</b> foi recebida!</p>"
            text_content = f"Olá {reserva.cliente.nome}, sua reserva #{reserva.codigo} foi recebida!"

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

    # --- LÓGICA NOVA: PEGAR DATAS BLOQUEADAS ---
    # Pegamos bloqueios gerais (dia todo) OU bloqueios específicos dessa praia
    bloqueios = Bloqueio.objects.filter(
        Q(praia__isnull=True) | Q(praia=praia)
    ).values_list('data', flat=True)
    
    # Transforma em uma lista de textos ["2026-02-12", "2026-02-15"] para o Javascript ler
    datas_bloqueadas = [b.strftime("%Y-%m-%d") for b in bloqueios]
    datas_bloqueadas_json = json.dumps(datas_bloqueadas)
    # --------------------------------------------

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            cliente = cliente_form.save()
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            reserva.praia_destino = praia
            reserva.tipo = 'passeio'
            reserva.status = 'pendente'
            reserva.valor = praia.valor if praia.valor else 0.00
            reserva.save()
            
            enviar_email_reserva(reserva, praia.nome)
            messages.success(request, f"Solicitação enviada! Verifique seu e-mail.")
            return redirect('reserva_confirmada')
        else:
            # Se deu erro (ex: data bloqueada), avisamos aqui
            messages.error(request, "Por favor, corrija os erros no formulário abaixo.")
    else:
        cliente_form = ClientePublicoForm()
        reserva_form = ReservaPublicaForm()

    return render(request, 'core/fazer_reserva.html', {
        'praia': praia,
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
        'sugestoes': sugestoes,
        'datas_bloqueadas': datas_bloqueadas_json, # <--- Enviamos para o HTML
    })

def fazer_reserva_transfer(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    sugestoes = Transfer.objects.filter().exclude(id=transfer.id)[:3]

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            cliente = cliente_form.save()
            
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            reserva.tipo = 'transfer'
            reserva.local_chegada = transfer.titulo
            reserva.status = 'pendente'
            reserva.valor = transfer.valor
            reserva.save()
            
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

def cadastro_parceiro(request):
    if request.method == 'POST':
        form = CadastroParceiroForm(request.POST)
        if form.is_valid():
            # 1. Pega os dados
            nome = form.cleaned_data['nome_completo']
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            telefone = form.cleaned_data['telefone']
            pix = form.cleaned_data['chave_pix']

            # 2. Cria o Usuário (INATIVO até confirmar email - ou ATIVO direto se preferir agilizar)
            # Vamos criar ATIVO direto pra simplificar o teste hoje, depois colocamos a confirmação de email?
            # Ou quer fazer com confirmação agora mesmo?
            # Vou fazer ATIVO direto pra você ver funcionando já, ok?
            
            user = User.objects.create_user(username=email, email=email, password=senha)
            user.first_name = nome
            user.save()

            # 3. Atualiza o perfil de Parceiro (que é criado automaticamente pelo Signal)
            parceiro = user.parceiro
            parceiro.telefone = telefone
            parceiro.chave_pix = pix
            parceiro.save()

            # 4. Manda pro Login com mensagem de sucesso
            messages.success(request, "Cadastro realizado! Faça login para começar a vender.")
            return redirect('login_parceiro')
    else:
        form = CadastroParceiroForm()

    return render(request, 'core/parceiro_cadastro.html', {'form': form})

def login_parceiro(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        user = authenticate(request, username=email, password=senha)
        if user is not None:
            login(request, user)
            return redirect('painel_parceiro')
        else:
            messages.error(request, "Email ou senha inválidos.")
    
    return render(request, 'core/parceiro_login.html')

@login_required(login_url='login_parceiro')
def painel_parceiro(request):
    # Garante que é um parceiro
    if not hasattr(request.user, 'parceiro'):
        return redirect('home')
        
    parceiro = request.user.parceiro
    reservas = parceiro.reservas.all().order_by('-data_agendamento')
    
    # Cálculo simples de comissão a receber
    total_a_receber = sum(r.valor_comissao for r in reservas if r.status_pagamento_comissao == 'pendente')
    
    context = {
        'parceiro': parceiro,
        'reservas': reservas,
        'total_a_receber': total_a_receber
    }
    return render(request, 'core/painel_parceiro.html', context)

def logout_parceiro(request):
    logout(request)
    return redirect('login_parceiro')

def nova_reserva_parceiro(request):
    return HttpResponse("Em breve: Formulário de Venda")