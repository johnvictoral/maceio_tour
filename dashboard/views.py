from django.shortcuts import render, redirect, get_object_or_404
import base64
import os
import io # <--- IMPORTANTE PARA O PDF NOVO
import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse # Adicionei JsonResponse para o calendário
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.utils.text import slugify
from django.utils.html import strip_tags # <--- IMPORTANTE PARA EMAIL
from django.core.mail import EmailMultiAlternatives # <--- IMPORTANTE PARA ANEXO

from weasyprint import HTML

# --- IMPORTAÇÕES DO REPORTLAB (PARA O VOUCHER AUTOMÁTICO) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Seus formulários
from .forms import (
    ImagemCarrosselForm, 
    ReciboManualForm, 
    GuiaForm, 
    ReservaEditForm, 
    ReservaManualForm, 
    PraiaForm, 
    ClienteForm,
    DepoimentoForm,
    CarrosselForm,
    PostForm,
    TransferForm
)

# Seus modelos
from core.models import Reserva, Cliente, Praia, Guia, ImagemCarrossel, Depoimento, Post, Transfer
from .utils import render_to_pdf

# =======================================================
# 1. FUNÇÕES AUXILIARES NOVAS (GERAR PDF E ENVIAR EMAIL)
# =======================================================

def gerar_voucher_pdf_interno(reserva):
    """Gera o PDF do Voucher na memória usando ReportLab (Rápido)"""
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
    """Função que monta o e-mail, gera o PDF e envia tudo"""
    try:
        print(f"--- DISPARANDO E-MAIL COM PDF PARA {reserva.cliente.email} ---")
        servico_nome = reserva.praia_destino.nome if reserva.praia_destino else (reserva.local_chegada or "Transfer")
        
        # 1. Gera o PDF
        pdf_buffer = gerar_voucher_pdf_interno(reserva)
        filename = f"Voucher_{reserva.codigo}.pdf"

        # 2. Renderiza o HTML do E-mail
        try:
            html_content = render_to_string('core/emails/reserva_confirmada.html', {
                'nome_cliente': reserva.cliente.nome,
                'codigo': reserva.codigo,
                'data_viagem': reserva.data_agendamento,
                'servico': servico_nome,
                'guia': reserva.guia,
            })
        except Exception as e:
            print(f"Erro Template Email: {e}")
            html_content = f"<p>Sua reserva #{reserva.codigo} foi confirmada!</p>"

        text_content = strip_tags(html_content)

        # 3. Monta e Envia
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
# 2. VIEWS (COM A NOVA LÓGICA NO DETALHE_RESERVA)
# =======================================================

class CustomLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = True

@login_required
def painel(request):
    # 1. Configurações de Data
    hoje = timezone.now()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # 2. Captura os filtros da URL
    status_filtro = request.GET.get('status')
    data_filtro = request.GET.get('data')
    busca = request.GET.get('busca')

    # Lógica de Filtros
    if not busca and not data_filtro:
        reservas = Reserva.objects.filter(data_agendamento__gte=hoje.date()).order_by('data_agendamento')
        if not status_filtro:
            reservas = reservas.filter(status__in=['pendente', 'confirmado'])
    else:
        reservas = Reserva.objects.all().order_by('-data_agendamento')

    if status_filtro:
        reservas = reservas.filter(status=status_filtro)
    if data_filtro:
        reservas = reservas.filter(data_agendamento__date=data_filtro)
    if busca:
        reservas = reservas.filter(
            Q(cliente__nome__icontains=busca) | 
            Q(cliente__email__icontains=busca) |
            Q(codigo__icontains=busca) |
            Q(id__icontains=busca)
        )

    # 3. Cálculos Financeiros (KPIs)
    faturamento_mes = Reserva.objects.filter(
        data_agendamento__month=mes_atual,
        data_agendamento__year=ano_atual,
        status__in=['confirmado', 'concluido']
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    reservas_hoje = Reserva.objects.filter(data_agendamento__date=hoje.date()).count()
    reservas_pendentes = Reserva.objects.filter(status='pendente').count()

    # 4. Dados para o Gráfico
    dados_grafico = []
    labels_grafico = []
    for i in range(5, -1, -1):
        data_ref = hoje - datetime.timedelta(days=i*30)
        fat_mensal = Reserva.objects.filter(
            data_agendamento__month=data_ref.month,
            data_agendamento__year=data_ref.year,
            status__in=['confirmado', 'concluido']
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        dados_grafico.append(float(fat_mensal))
        labels_grafico.append(data_ref.strftime("%B/%Y"))

    context = {
        'reservas': reservas,
        'status_filtro': status_filtro,
        'data_filtro': data_filtro,
        'busca': busca,
        'reservas_hoje': reservas_hoje,
        'reservas_pendentes': reservas_pendentes,
        'faturamento_mes': faturamento_mes,
        'total_clientes': Cliente.objects.count(),
        'labels_grafico': labels_grafico,
        'dados_grafico': dados_grafico,
    }
    return render(request, 'dashboard/painel.html', context)

@login_required
def gerenciar_banner(request):
    if request.method == 'POST' and 'upload_image' in request.POST:
        form = ImagemCarrosselForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_banner')
    if request.method == 'POST' and 'delete_image' in request.POST:
        imagem_id = request.POST.get('delete_image')
        imagem_para_deletar = get_object_or_404(ImagemCarrossel, id=imagem_id)
        imagem_para_deletar.delete()
        return redirect('gerenciar_banner')

    imagens = ImagemCarrossel.objects.all()
    form = ImagemCarrosselForm()
    context = {'imagens': imagens, 'form': form}
    return render(request, 'dashboard/gerenciar_banner.html', context)

# --- AQUI ESTÁ A VIEW MODIFICADA (ATENÇÃO!) ---
@login_required
def detalhe_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    guias_disponiveis = Guia.objects.filter(ativo=True)
    
    if request.method == 'POST':
        # --- Lógica de Atualizar Status (Botões Coloridos) ---
        if 'status' in request.POST:
            novo_status = request.POST.get('status')
            if novo_status in ['confirmado', 'concluido', 'cancelado']:
                reserva.status = novo_status
                reserva.save()
                
                # NOVO: SE CONFIRMOU, DISPARA O E-MAIL
                if novo_status == 'confirmado':
                    disparar_email_confirmacao(request, reserva)
                else:
                    messages.success(request, f"Status atualizado para {reserva.get_status_display()}!")
                
                return redirect('detalhe_reserva', reserva_id=reserva.id)
        
        # --- Lógica de Atribuir Guia ---
        if 'guia' in request.POST:
            guia_id = request.POST.get('guia')
            if guia_id:
                guia_selecionado = get_object_or_404(Guia, id=guia_id)
                reserva.guia = guia_selecionado 
                reserva.save()
                messages.success(request, f"Guia {guia_selecionado.nome} atribuído com sucesso!")
                
                # NOVO: SE JÁ ESTAVA CONFIRMADO, REENVIA O E-MAIL COM O GUIA
                if reserva.status == 'confirmado':
                    disparar_email_confirmacao(request, reserva)
            else:
                reserva.guia = None
                reserva.save()
                messages.info(request, "Guia removido.")
            
            return redirect('detalhe_reserva', reserva_id=reserva.id)

    context = {'reserva': reserva, 'guias': guias_disponiveis}
    return render(request, 'dashboard/detalhe_reserva.html', context)

# ... (MANTENHA O RESTO DAS VIEWS IGUAIS ABAIXO) ...
@login_required
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        form = ReservaEditForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            return redirect('detalhe_reserva', reserva_id=reserva.id)
    else:
        form = ReservaEditForm(instance=reserva)
    context = {'form': form, 'reserva': reserva}
    return render(request, 'dashboard/editar_reserva.html', context)

@login_required
def excluir_reserva(request, reserva_id):
    if request.method == 'POST':
        reserva = get_object_or_404(Reserva, id=reserva_id)
        reserva.delete()
        return redirect('painel')
    else:
        return redirect('painel')

# --- VIEWS DE GERENCIAMENTO DE PESSOAS ---

@login_required
def lista_clientes(request):
    todos_os_clientes = Cliente.objects.all().order_by('nome')
    context = {'clientes': todos_os_clientes}
    return render(request, 'dashboard/lista_clientes.html', context)

@login_required
def excluir_cliente(request, cliente_id):
    if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.delete()
        return redirect('lista_clientes')
    else:
        return redirect('lista_clientes')

@login_required
def lista_parceiros(request):
    if request.method == 'POST':
        form = GuiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_parceiros')
    else:
        form = GuiaForm()
    todos_os_parceiros = Guia.objects.all().order_by('nome')
    context = {'parceiros': todos_os_parceiros, 'form': form}
    return render(request, 'dashboard/lista_parceiros.html', context)

@login_required
def excluir_parceiro(request, guia_id):
    if request.method == 'POST':
        guia = get_object_or_404(Guia, id=guia_id)
        guia.delete()
        return redirect('lista_parceiros')
    else:
        return redirect('lista_parceiros')

# --- VIEWS DE PDF E CALENDÁRIO ---

@login_required
def gerar_recibo_pdf(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if settings.DEBUG:
        img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    else:
        img_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
        if not os.path.exists(img_path):
             img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    
    logo_data = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        logo_data = f"data:image/png;base64,{encoded_string}"
    
    context = {
        'reserva': reserva,
        'user': request.user,
        'logo_data': logo_data
    }
    
    html_string = render_to_string('dashboard/voucher_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'voucher_reserva_{reserva.id}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def gerar_recibo_manual(request):
    if request.method == 'POST':
        form = ReciboManualForm(request.POST)
        if form.is_valid():
            dados_recibo = form.cleaned_data
            if settings.DEBUG:
                logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
            else:
                logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
                if not os.path.exists(logo_path):
                     logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')

            context = {
                'recibo': dados_recibo, 
                'user': request.user,
                'logo_path': logo_path 
            }

            html_string = render_to_string('dashboard/recibo_manual_pdf.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            num_recibo = dados_recibo.get('numero_recibo') or 'avulso'
            filename = f"recibo_{num_recibo}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
    else:
        form = ReciboManualForm()
    return render(request, 'dashboard/gerar_recibo_manual.html', {'form': form})

@login_required
def gerar_recibo_financeiro(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if settings.DEBUG:
        img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    else:
        img_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
        if not os.path.exists(img_path):
             img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    
    logo_data = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        logo_data = f"data:image/png;base64,{encoded_string}"
    
    context = {
        'reserva': reserva,
        'user': request.user,
        'logo_data': logo_data 
    }
    
    html_string = render_to_string('dashboard/recibo_pagamento.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'recibo_pagamento_{reserva.id}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def calendario_view(request):
    return render(request, 'dashboard/calendario.html')

@login_required
def calendario_api(request):
    todas_as_reservas = Reserva.objects.filter(status__in=['pendente', 'confirmado', 'concluido'])
    eventos = []
    for reserva in todas_as_reservas:
        cor = '#ffc107'
        if reserva.status == 'confirmado': cor = '#198754'
        elif reserva.status == 'concluido': cor = '#6c757d'
        eventos.append({
            'title': f"{reserva.get_tipo_display()} - {reserva.cliente.nome}",
            'start': reserva.data_agendamento.isoformat(),
            'allDay': False,
            'url': f"/dashboard/reserva/{reserva.id}/",
            'backgroundColor': cor,
            'borderColor': cor,
        })
    return JsonResponse(eventos, safe=False)

@login_required
def nova_reserva_manual(request):
    initial_data = {}
    if 'cliente_id' in request.GET:
        cliente_pre = get_object_or_404(Cliente, id=request.GET.get('cliente_id'))
        initial_data = {
            'nome_cliente': cliente_pre.nome,
            'sobrenome_cliente': cliente_pre.sobrenome,
            'email_cliente': cliente_pre.email,
            'telefone_cliente': cliente_pre.telefone,
        }

    if request.method == 'POST':
        form = ReservaManualForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            cliente_obj, created = Cliente.objects.update_or_create(
                email=dados['email_cliente'],
                defaults={
                    'nome': dados['nome_cliente'],
                    'sobrenome': dados['sobrenome_cliente'],
                    'telefone': dados['telefone_cliente'],
                }
            )
            nova_reserva = Reserva(
                cliente=cliente_obj,
                tipo=dados['tipo_servico'],
                data_agendamento=dados['data_agendamento'],
                numero_passageiros=dados['numero_passageiros'],
                valor=dados['valor'],
                informacoes_voo=dados['informacoes_voo'],
                status='confirmado'
            )
            if dados['tipo_servico'] == 'passeio':
                nova_reserva.praia_destino = dados['praia_selecionada']
                nova_reserva.local_partida = "A combinar (Ver Obs)"
            else:
                nova_reserva.local_partida = dados['local_partida']
                nova_reserva.local_chegada = dados['local_chegada']
            
            nova_reserva.save()

            if 'salvar_adicionar' in request.POST:
                return redirect(f"{reverse('nova_reserva_manual')}?cliente_id={cliente_obj.id}")
            else:
                return redirect('painel')
    else:
        form = ReservaManualForm(initial=initial_data)

    return render(request, 'dashboard/nova_reserva_manual.html', {'form': form})

@login_required
def lista_praias(request):
    praias = Praia.objects.all().order_by('nome')
    return render(request, 'dashboard/lista_praias.html', {'praias': praias})

@login_required
def nova_praia(request):
    if request.method == 'POST':
        form = PraiaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Passeio cadastrado com sucesso!')
            return redirect('lista_praias')
    else:
        form = PraiaForm()
    return render(request, 'dashboard/form_praia.html', {'form': form, 'titulo': 'Novo Passeio'})

@login_required
def editar_praia(request, praia_id):
    praia = get_object_or_404(Praia, id=praia_id)
    if request.method == 'POST':
        form = PraiaForm(request.POST, request.FILES, instance=praia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Passeio atualizado!')
            return redirect('lista_praias')
    else:
        form = PraiaForm(instance=praia)
    return render(request, 'dashboard/form_praia.html', {'form': form, 'titulo': 'Editar Passeio'})

@login_required
def excluir_praia(request, praia_id):
    praia = get_object_or_404(Praia, id=praia_id)
    praia.delete()
    messages.success(request, 'Praia removida.')
    return redirect('lista_praias')

@login_required
def novo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado!')
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'dashboard/form_cliente.html', {'form': form, 'titulo': 'Novo Cliente'})

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado!')
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'dashboard/form_cliente.html', {'form': form, 'titulo': f'Editar {cliente.nome}'})

@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('-id')
    return render(request, 'dashboard/lista_clientes.html', {'clientes': clientes})

@login_required
def gerar_voucher(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    data = {
        'reserva': reserva,
        'empresa': 'JVC Turismo',
        'telefone_empresa': '(82) 99999-9999',
        'site': request.build_absolute_uri('/')[:-1],
    }
    pdf = render_to_pdf('dashboard/voucher_pdf.html', data)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Voucher_{reserva.id}_{reserva.cliente.nome}.pdf"
        content = f"inline; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Erro ao gerar PDF")

@login_required
def lista_depoimentos(request):
    depoimentos = Depoimento.objects.all().order_by('-id')
    return render(request, 'dashboard/lista_depoimentos.html', {'depoimentos': depoimentos})

@login_required
def novo_depoimento(request):
    if request.method == 'POST':
        form = DepoimentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Depoimento adicionado!')
            return redirect('lista_depoimentos')
    else:
        form = DepoimentoForm()
    return render(request, 'dashboard/form_depoimento.html', {'form': form, 'titulo': 'Novo Depoimento'})

@login_required
def excluir_depoimento(request, depoimento_id):
    depoimento = get_object_or_404(Depoimento, id=depoimento_id)
    depoimento.delete()
    messages.success(request, 'Depoimento removido.')
    return redirect('lista_depoimentos')

@login_required
def lista_posts(request):
    posts = Post.objects.all().order_by('-data_publicacao')
    return render(request, 'dashboard/lista_posts.html', {'posts': posts})

@login_required
def novo_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if not post.slug:
                post.slug = slugify(post.titulo)
            post.save()
            messages.success(request, 'Postagem criada com sucesso!')
            return redirect('lista_posts')
    else:
        form = PostForm()
    return render(request, 'dashboard/form_post.html', {'form': form, 'titulo': 'Nova Postagem'})

@login_required
def editar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Postagem atualizada!')
            return redirect('lista_posts')
    else:
        form = PostForm(instance=post)
    return render(request, 'dashboard/form_post.html', {'form': form, 'titulo': f'Editar: {post.titulo}'})

@login_required
def excluir_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, 'Postagem removida.')
    return redirect('lista_posts')

@login_required
def gerenciar_carrossel(request):
    imagens = ImagemCarrossel.objects.all().order_by('-id')
    return render(request, 'dashboard/lista_carrossel.html', {'imagens': imagens})

@login_required
def novo_carrossel(request):
    if request.method == 'POST':
        form = CarrosselForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner adicionado com sucesso!')
            return redirect('gerenciar_carrossel')
    else:
        form = CarrosselForm()
    return render(request, 'dashboard/form_carrossel.html', {'form': form, 'titulo': 'Novo Banner'})

@login_required
def editar_carrossel(request, item_id):
    item = get_object_or_404(ImagemCarrossel, id=item_id)
    if request.method == 'POST':
        form = CarrosselForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner atualizado!')
            return redirect('gerenciar_carrossel')
    else:
        form = CarrosselForm(instance=item)
    return render(request, 'dashboard/form_carrossel.html', {'form': form, 'titulo': 'Editar Banner'})

@login_required
def excluir_carrossel(request, item_id):
    item = get_object_or_404(ImagemCarrossel, id=item_id)
    item.delete()
    messages.success(request, 'Banner removido.')
    return redirect('gerenciar_carrossel')

@login_required
def lista_transfers(request):
    transfers = Transfer.objects.all()
    return render(request, 'dashboard/lista_transfers.html', {'transfers': transfers})

@login_required
def novo_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transfer criado com sucesso!')
            return redirect('lista_transfers')
    else:
        form = TransferForm()
    return render(request, 'dashboard/form_transfer.html', {'form': form, 'titulo': 'Novo Transfer'})

@login_required
def editar_transfer(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    if request.method == 'POST':
        form = TransferForm(request.POST, request.FILES, instance=transfer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transfer atualizado!')
            return redirect('lista_transfers')
    else:
        form = TransferForm(instance=transfer)
    return render(request, 'dashboard/form_transfer.html', {'form': form, 'titulo': 'Editar Transfer'})

@login_required
def excluir_transfer(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    transfer.delete()
    messages.success(request, 'Transfer removido.')
    return redirect('lista_transfers')

@login_required
def lista_reservas(request):
    reservas = Reserva.objects.all().order_by('-id')
    status_filtro = request.GET.get('status')
    if status_filtro:
        reservas = reservas.filter(status=status_filtro)
    data_filtro = request.GET.get('data')
    if data_filtro:
        reservas = reservas.filter(data_agendamento__date=data_filtro)
    busca = request.GET.get('busca')
    if busca:
        reservas = reservas.filter(
            Q(cliente__nome__icontains=busca) | 
            Q(cliente__email__icontains=busca) |
            Q(id__icontains=busca)
        )
    context = {
        'reservas': reservas,
        'status_filtro': status_filtro,
        'data_filtro': data_filtro,
        'busca': busca
    }
    return render(request, 'dashboard/lista_reservas.html', context)