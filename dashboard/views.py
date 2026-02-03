from django.shortcuts import render, redirect, get_object_or_404
import base64
import os              # <--- ADICIONE
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from weasyprint import HTML
from django.contrib.auth.views import LoginView # <--- ESSA LINHA RESOLVE O SEU ERRO ATUAL
from django.utils.text import slugify
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
    CarrosselForm
)

# Seus modelos (Vindos do core)
from core.models import Reserva, Cliente, Praia, Guia, ImagemCarrossel, Depoimento, Post,Transfer
from .forms import PostForm
from .forms import TransferForm
#######
from .utils import render_to_pdf # Importe a função nova
# --- VIEWS DE AUTENTICAÇÃO E PAINEL PRINCIPAL ---

class CustomLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = True

@login_required
def painel(request):
    # 1. Pegamos os dados que vêm do filtro (URL)
    status_filtro = request.GET.get('status')
    data_filtro = request.GET.get('data')
    busca = request.GET.get('busca')

    # 2. Query Base: Começamos pegando TUDO ordenado por data
    reservas = Reserva.objects.all().order_by('data_agendamento')

    # --- LÓGICA DE FILTROS ---

    # A. Filtro por STATUS
    if status_filtro:
        # Se o usuário escolheu um status específico, mostramos ele
        reservas = reservas.filter(status=status_filtro)
    elif not data_filtro and not busca:
        # Se NÃO tem filtro nenhum (acabou de entrar na página),
        # mostramos apenas o padrão do dashboard: Pendente e Confirmado
        reservas = reservas.filter(status__in=['pendente', 'confirmado'])

    # B. Filtro por DATA
    if data_filtro:
        reservas = reservas.filter(data_agendamento__date=data_filtro)

    # C. Filtro de BUSCA (Nome, Email ou ID)
    if busca:
        reservas = reservas.filter(
            Q(cliente__nome__icontains=busca) | 
            Q(cliente__email__icontains=busca) |
            Q(id__icontains=busca)
        )

    # --- FIM DA LÓGICA ---

    # 3. KPIs (Contadores do topo da tela)
    # Estes NÃO mudam com o filtro, mostram sempre o total geral
    context = {
        'reservas': reservas, # A lista filtrada
        
        # Filtros (para o HTML lembrar o que foi selecionado)
        'status_filtro': status_filtro,
        'data_filtro': data_filtro,
        'busca': busca,

        # Contadores (KPIs)
        'reservas_hoje': Reserva.objects.filter(data_agendamento__date=timezone.now().date()).count(),
        'reservas_pendentes': Reserva.objects.filter(status='pendente').count(),
        'faturamento_mes': 0, # Sua lógica de faturamento
        'total_clientes': Cliente.objects.count(),
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

# --- VIEWS DE GERENCIAMENTO DE RESERVAS ---

@login_required
def detalhe_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    guias_disponiveis = Guia.objects.filter(ativo=True)
    
    if request.method == 'POST':
        # Lógica de Atualizar Status
        if 'status' in request.POST:
            novo_status = request.POST.get('status')
            if novo_status in ['confirmado', 'concluido', 'cancelado']:
                reserva.status = novo_status
                reserva.save()
                return redirect('detalhe_reserva', reserva_id=reserva.id)
        
        # Lógica de Atribuir Guia (O ERRO ESTAVA AQUI)
        if 'guia' in request.POST:
            guia_id = request.POST.get('guia')
            if guia_id:
                guia_selecionado = get_object_or_404(Guia, id=guia_id)
                # CORREÇÃO: Mudamos de 'guia_atribuido' para 'guia'
                reserva.guia = guia_selecionado 
            else:
                # CORREÇÃO: Mudamos de 'guia_atribuido' para 'guia'
                reserva.guia = None
            
            reserva.save()
            return redirect('detalhe_reserva', reserva_id=reserva.id)

    context = {'reserva': reserva, 'guias': guias_disponiveis}
    return render(request, 'dashboard/detalhe_reserva.html', context)

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
    
    # 1. Tenta achar a imagem
    if settings.DEBUG:
        img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    else:
        img_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
        if not os.path.exists(img_path):
             img_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    
    # 2. Converte a imagem para Base64 (Texto)
    logo_data = ""
    if os.path.exists(img_path):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        logo_data = f"data:image/png;base64,{encoded_string}"
    
    # 3. Manda para o HTML
    context = {
        'reserva': reserva,
        'user': request.user,
        'logo_data': logo_data # <--- Agora usamos 'logo_data'
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
            
            # --- LÓGICA DA IMAGEM TAMBÉM NO MANUAL ---
            if settings.DEBUG:
                logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
            else:
                logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
                if not os.path.exists(logo_path):
                     logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
            # -----------------------------------------

            # Adiciona a logo ao contexto
            context = {
                'recibo': dados_recibo, 
                'user': request.user,
                'logo_path': logo_path 
            }

            html_string = render_to_string('dashboard/recibo_manual_pdf.html', context)
            
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf = html.write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            # Tratamento seguro para o nome do arquivo (caso não tenha número)
            num_recibo = dados_recibo.get('numero_recibo') or 'avulso'
            filename = f"recibo_{num_recibo}.pdf"
            
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
    else:
        form = ReciboManualForm()
    
    return render(request, 'dashboard/gerar_recibo_manual.html', {'form': form})

@login_required
def gerar_recibo_financeiro(request, reserva_id):
    # Pega a reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Lógica da Imagem (Base64) - A mesma que usamos no voucher
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
    
    # ATENÇÃO: Chama um HTML novo (recibo_pagamento.html) para não mexer no voucher
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
    # Verifica se já temos dados de cliente pré-carregados (do passo "Salvar e Adicionar Outro")
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
            
            # 1. Cria ou Atualiza o Cliente
            cliente_obj, created = Cliente.objects.update_or_create(
                email=dados['email_cliente'],
                defaults={
                    'nome': dados['nome_cliente'],
                    'sobrenome': dados['sobrenome_cliente'],
                    'telefone': dados['telefone_cliente'],
                }
            )

            # 2. Cria a Reserva
            nova_reserva = Reserva(
                cliente=cliente_obj,
                tipo=dados['tipo_servico'],
                data_agendamento=dados['data_agendamento'],
                numero_passageiros=dados['numero_passageiros'],
                valor=dados['valor'],
                informacoes_voo=dados['informacoes_voo'],
                status='confirmado' # Já nasce confirmada pois foi você quem fez
            )

            # Preenche os campos específicos dependendo do tipo
            if dados['tipo_servico'] == 'passeio':
                nova_reserva.praia_destino = dados['praia_selecionada']
                nova_reserva.local_partida = "A combinar (Ver Obs)" # Valor padrão
            else:
                nova_reserva.local_partida = dados['local_partida']
                nova_reserva.local_chegada = dados['local_chegada']
            
            nova_reserva.save()

            # 3. Verifica qual botão foi clicado
            if 'salvar_adicionar' in request.POST:
                # Redireciona para a mesma página, mas passando o ID do cliente para preencher automático
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
        # O ERRO ESTAVA AQUI: Faltava o request.FILES
        form = PraiaForm(request.POST, request.FILES) 
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Passeio cadastrado com sucesso!')
            return redirect('lista_praias') # Verifique se o nome da sua rota é esse mesmo
    else:
        form = PraiaForm()
    
    return render(request, 'dashboard/form_praia.html', {'form': form, 'titulo': 'Novo Passeio'})

@login_required
def editar_praia(request, praia_id):
    praia = get_object_or_404(Praia, id=praia_id)
    if request.method == 'POST':
        # AQUI TAMBÉM PRECISA DO request.FILES
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

# --- GESTÃO DE CLIENTES (Novo) ---

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
    clientes = Cliente.objects.all().order_by('-id') # Mostra os mais novos primeiro
    return render(request, 'dashboard/lista_clientes.html', {'clientes': clientes})

@login_required
def gerar_voucher(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    data = {
        'reserva': reserva,
        'empresa': 'JVC Turismo',
        'telefone_empresa': '(82) 99999-9999',
        'site': request.build_absolute_uri('/')[:-1], # Pega o URL do site atual
    }
    
    # Renderiza o PDF
    pdf = render_to_pdf('dashboard/voucher_pdf.html', data)
    
    # Se quiser que faça download direto, mude para 'attachment'. 
    # 'inline' abre no navegador.
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

# --- GESTÃO DE BLOG ---

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
            # Gera o slug automaticamente se não existir
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

# --- GESTÃO DE CARROSSEL ---

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

# --- GESTÃO DE TRANSFERS ---
@login_required
def lista_transfers(request):
    transfers = Transfer.objects.all()
    return render(request, 'dashboard/lista_transfers.html', {'transfers': transfers})

@login_required
def novo_transfer(request):
    if request.method == 'POST':
        # ADICIONE O request.FILES AQUI:
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
        # ADICIONE O request.FILES AQUI TAMBÉM:
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
    # 1. Pega TODAS as reservas, da mais nova para a mais antiga
    reservas = Reserva.objects.all().order_by('-id')

    # --- INÍCIO DA LÓGICA DE FILTROS ---

    # Filtro por STATUS
    status_filtro = request.GET.get('status')
    if status_filtro:
        reservas = reservas.filter(status=status_filtro)

    # Filtro por DATA
    data_filtro = request.GET.get('data')
    if data_filtro:
        # __date filtra ignorando a hora (apenas dia/mês/ano)
        reservas = reservas.filter(data_agendamento__date=data_filtro)

    # Filtro de BUSCA (Nome, Email ou ID da reserva)
    busca = request.GET.get('busca')
    if busca:
        reservas = reservas.filter(
            Q(cliente__nome__icontains=busca) | 
            Q(cliente__email__icontains=busca) |
            Q(id__icontains=busca)
        )

    # --- FIM DA LÓGICA ---

    context = {
        'reservas': reservas,
        # Passamos os filtros de volta para o HTML para manter os campos preenchidos
        'status_filtro': status_filtro,
        'data_filtro': data_filtro,
        'busca': busca
    }
    
    return render(request, 'dashboard/lista_reservas.html', context)