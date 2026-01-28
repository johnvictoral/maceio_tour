import json # Adicione este import no topo
from django.shortcuts import render, get_object_or_404,redirect
from .models import ImagemCarrossel, Praia,Transfer,Depoimento,Post
from .forms import ClientePublicoForm, ReservaPublicaForm
from django.contrib import messages
from django.conf import settings
from .mares_data import DADOS_MARES_2026
import os
from datetime import datetime
def home(request):
    imagens_carrossel = ImagemCarrossel.objects.filter(ativo=True)
    praias = Praia.objects.filter(ativo=True)
    transfers = Transfer.objects.all()
    depoimentos = Depoimento.objects.filter(ativo=True).order_by('-id')[:3]

    # --- VERIFIQUE SE ESTA LINHA EXISTE ---
    # Ela pega apenas os publicados, ordenados pelo mais novo
    posts_recentes = Post.objects.filter(status='publicado').order_by('-data_publicacao')[:3]
    
    context = {
        'imagens_carrossel': imagens_carrossel,
        'praias': praias,
        'transfers': transfers,
        'depoimentos': depoimentos,
        'posts_recentes': posts_recentes, # --- E SE ELA ESTÁ AQUI NO CONTEXTO ---
    }
    
    return render(request, 'core/home.html', context)

def detalhe_praia(request, slug):
    # Pega a praia principal que o cliente está vendo
    praia = get_object_or_404(Praia, slug=slug)

    # --- NOVA LÓGICA ---
    # Busca até 3 outras praias no banco de dados,
    # excluindo a que já está sendo exibida.
    sugestoes = Praia.objects.exclude(slug=slug)[:3]

    # Adiciona tanto a praia principal quanto as sugestões ao contexto
    context = {
        'praia': praia,
        'sugestoes': sugestoes, # Adiciona a lista de sugestões
    }
    return render(request, 'core/detalhe_praia.html', context)

# View para a página "Sobre Nós"
def sobre_nos_view(request):
    return render(request, 'core/sobre_nos.html')

# View para a página "Contato"
def contato_view(request):
    return render(request, 'core/contato.html')

# core/views.py
import json
from django.conf import settings
import os
# Remova 'from datetime import datetime' se não estiver sendo usado em outras partes da view

# ... (outras views) ...

# core/views.py

def tabua_de_mares_view(request):
    # 1. Lista de meses disponíveis (pegando as chaves do dicionário)
    meses_disponiveis = list(DADOS_MARES_2026.keys())

    # 2. Lógica de seleção do mês
    mes_selecionado = request.GET.get('mes')
    
    # Se não tiver mês selecionado na URL, tenta pegar o mês atual do sistema
    if not mes_selecionado:
        mes_map_num = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        mes_atual_nome = mes_map_num.get(datetime.now().month)
        
        # Verifica se temos dados para o mês atual, senão pega o primeiro da lista
        if mes_atual_nome in DADOS_MARES_2026:
            mes_selecionado = mes_atual_nome
        elif meses_disponiveis:
            mes_selecionado = meses_disponiveis[0]

    # 3. Pega os dados do mês escolhido
    # Usamos .get() para evitar erro se o mês não existir
    dados_do_mes = DADOS_MARES_2026.get(mes_selecionado, [])

    # --- SUA LÓGICA DE TENDÊNCIA (MANTIDA E ADAPTADA) ---
    
    altura_anterior = None

    # Passa por cada dia do mês
    for dia_dados in dados_do_mes:
        mares_do_dia = dia_dados['mares']
        
        # Passa por cada medição de maré no dia
        for mare_atual in mares_do_dia:
            # Se já tivermos uma medição anterior para comparar
            if altura_anterior is not None:
                if mare_atual['altura'] > altura_anterior:
                    mare_atual['tendencia'] = 'subindo'
                elif mare_atual['altura'] < altura_anterior:
                    mare_atual['tendencia'] = 'descendo'
                else:
                    mare_atual['tendencia'] = 'estavel'
            
            # Atualiza a variável para a próxima iteração
            altura_anterior = mare_atual['altura']

    # Tratamento especial para a primeiríssima maré do mês
    if dados_do_mes and dados_do_mes[0]['mares']:
        primeira_mare = dados_do_mes[0]['mares'][0]
        
        # Se não tem tendência (porque não tinha anterior), comparamos com a próxima
        if 'tendencia' not in primeira_mare:
            # Verifica se existe uma segunda maré no mesmo dia
            if len(dados_do_mes[0]['mares']) > 1:
                segunda_mare = dados_do_mes[0]['mares'][1]
                if primeira_mare['altura'] < segunda_mare['altura']:
                    primeira_mare['tendencia'] = 'subindo' # Se a próxima é maior, essa estava subindo (início da subida)
                else:
                    primeira_mare['tendencia'] = 'descendo'
            else:
                primeira_mare['tendencia'] = 'estavel'

    context = {
        'tabela_mares': dados_do_mes,
        'meses_disponiveis': meses_disponiveis,
        'mes_selecionado': mes_selecionado,
    }
    
    # Certifique-se que o nome do template aqui é o mesmo que você está usando
    return render(request, 'core/tabua_de_mares.html', context)

def detalhe_transfer_view(request, slug):
    transfer = get_object_or_404(Transfer, slug=slug)
    context = {
        'transfer': transfer,
    }
    return render(request, 'core/detalhe_transfer.html', context)

def detalhe_post(request, slug):
    post = get_object_or_404(Post, slug=slug, status='publicado')
    
    # Busca 3 outros posts (exceto o atual) para mostrar na barra lateral
    outros_posts = Post.objects.filter(status='publicado').exclude(id=post.id).order_by('-data_publicacao')[:3]
    
    return render(request, 'core/detalhe_post.html', {
        'post': post, 
        'outros_posts': outros_posts
    })

def lista_de_posts(request):
    # Pega todos os posts publicados, do mais novo para o mais antigo
    posts = Post.objects.filter(status='publicado').order_by('-data_publicacao')
    return render(request, 'core/lista_posts.html', {'posts': posts})

def fazer_reserva_passeio(request, praia_id):
    praia = get_object_or_404(Praia, id=praia_id)
    
    # Busca 3 sugestões de outros passeios para a barra lateral
    sugestoes = Praia.objects.filter(ativo=True).exclude(id=praia.id)[:3]

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            # 1. Salva o Cliente
            cliente = cliente_form.save()
            
            # 2. Prepara a Reserva (mas não salva ainda)
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            reserva.praia_destino = praia # Vincula o passeio escolhido
            reserva.tipo = 'passeio'
            reserva.status = 'pendente'
            
            # Calcula valor total (se a praia tiver preço cadastrado)
            # Se seu model Praia tem campo 'preco', descomente abaixo:
            # reserva.valor = reserva.numero_passageiros * praia.preco 
            
            # 3. Salva a Reserva
            reserva.save()
            
            messages.success(request, f"Reserva para {praia.nome} realizada com sucesso! Entraremos em contato.")
            return redirect('reserva_confirmada') # Ou redirecionar para uma página de obrigado
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
    
    # Sugere outros transfers
    sugestoes = Transfer.objects.filter().exclude(id=transfer.id)[:3]

    if request.method == 'POST':
        cliente_form = ClientePublicoForm(request.POST)
        reserva_form = ReservaPublicaForm(request.POST)
        
        if cliente_form.is_valid() and reserva_form.is_valid():
            cliente = cliente_form.save()
            
            reserva = reserva_form.save(commit=False)
            reserva.cliente = cliente
            # Aqui vinculamos o transfer, não a praia
            # (Certifique-se que seu model Reserva tem um campo para transfer, 
            # ou use o campo de observação se não tiver)
            reserva.tipo = 'transfer'
            reserva.local_chegada = transfer.titulo # Salvamos o nome do transfer como destino
            reserva.status = 'pendente'
            reserva.valor = transfer.valor # Pega o valor do cadastro
            reserva.save()
            
            messages.success(request, f"Solicitação de Transfer '{transfer.titulo}' enviada!")
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