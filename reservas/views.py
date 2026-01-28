# reservas/views.py

import mercadopago
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from core.models import Praia,Transfer
from core.models import Cliente, Reserva
from core.models import Post
from .forms import PostForm
from django.utils.text import slugify
# CORREÇÃO PRINCIPAL: Adicionamos ReservaTransferForm à lista de imports
from .forms import ReservaPasseioForm, ClienteForm, ReservaTransferForm
from .forms import TransferForm


def fazer_reserva_passeio(request, slug_da_praia):
    praia_selecionada = get_object_or_404(Praia, slug=slug_da_praia)

    if request.method == 'POST':
        cliente_existente = None
        email = request.POST.get('email')
        if email:
            try:
                cliente_existente = Cliente.objects.get(email=email)
            except Cliente.DoesNotExist:
                pass
        
        cliente_form = ClienteForm(request.POST, instance=cliente_existente)
        reserva_form = ReservaPasseioForm(request.POST)

        if cliente_form.is_valid() and reserva_form.is_valid():
            cliente = cliente_form.save()

            nova_reserva = reserva_form.save(commit=False)
            nova_reserva.cliente = cliente
            nova_reserva.praia_destino = praia_selecionada
            nova_reserva.tipo = 'passeio'
            nova_reserva.valor = praia_selecionada.valor
            nova_reserva.save()
            
            return redirect('reserva_sucesso')
    else:
        cliente_form = ClienteForm()
        reserva_form = ReservaPasseioForm()

    context = {
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
        'praia': praia_selecionada
    }
    return render(request, 'reservas/fazer_reserva.html', context)


def solicitar_transfer(request):
    # Define os formulários como vazios no início
    cliente_form = ClienteForm()
    reserva_form = ReservaTransferForm()

    if request.method == 'POST':
        cliente_existente = None
        email = request.POST.get('email')
        if email:
            try:
                # Tenta encontrar um cliente com o e-mail fornecido
                cliente_existente = Cliente.objects.get(email=email)
            except Cliente.DoesNotExist:
                pass # Nenhum cliente encontrado, o que está ok

        # Instancia o formulário, passando o cliente existente se ele foi encontrado
        cliente_form = ClienteForm(request.POST, instance=cliente_existente)
        reserva_form = ReservaTransferForm(request.POST)

        if cliente_form.is_valid() and reserva_form.is_valid():
            # O .save() do ModelForm já sabe se deve CRIAR ou ATUALIZAR
            cliente = cliente_form.save()

            nova_reserva = reserva_form.save(commit=False)
            nova_reserva.cliente = cliente
            nova_reserva.tipo = 'transfer'
            nova_reserva.save()
            return redirect('reserva_sucesso')

    context = {
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
    }
    return render(request, 'reservas/solicitar_transfer.html', context)


def reserva_sucesso(request):
    return render(request, 'reservas/reserva_sucesso.html')


def reserva_falha(request):
    return render(request, 'reservas/reserva_falha.html')


def reserva_pendente(request):
    return render(request, 'reservas/reserva_pendente.html')

def fazer_reserva_transfer(request, slug):
    transfer_selecionado = get_object_or_404(Transfer, slug=slug)

    # Se o método for POST (envio do formulário)
    if request.method == 'POST':
        cliente_existente = None
        email = request.POST.get('email')
        if email:
            try:
                # Tenta encontrar um cliente com o e-mail fornecido
                cliente_existente = Cliente.objects.get(email=email)
            except Cliente.DoesNotExist:
                pass # Nenhum cliente encontrado, o que está ok

        # Instancia o formulário, passando o cliente existente se ele foi encontrado
        cliente_form = ClienteForm(request.POST, instance=cliente_existente)
        reserva_form = ReservaTransferForm(request.POST)

        if cliente_form.is_valid() and reserva_form.is_valid():
            # O .save() do cliente_form já sabe se deve CRIAR um novo ou ATUALIZAR o existente
            cliente = cliente_form.save()

            nova_reserva = reserva_form.save(commit=False)
            nova_reserva.cliente = cliente
            nova_reserva.tipo = 'transfer'
            nova_reserva.valor = transfer_selecionado.valor
            nova_reserva.local_partida = transfer_selecionado.origem
            nova_reserva.local_chegada = transfer_selecionado.destino
            nova_reserva.save()

            return redirect('reserva_sucesso')

    # Se o método for GET (primeiro acesso à página)
    else:
        cliente_form = ClienteForm()
        reserva_form = ReservaTransferForm()

    context = {
        'cliente_form': cliente_form,
        'reserva_form': reserva_form,
        'transfer': transfer_selecionado
    }
    return render(request, 'reservas/fazer_reserva_transfer.html', context)

# --- GESTÃO DE TRANSFERS ---
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

