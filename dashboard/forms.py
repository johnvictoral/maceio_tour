# dashboard/forms.py

from django import forms
from core.models import ImagemCarrossel,Guia,Praia, Transfer, Cliente
from core.models import Reserva, Cliente
from core.models import Depoimento,Post,ImagemCarrossel
from core.models import Bloqueio
from ckeditor.widgets import CKEditorWidget

class ImagemCarrosselForm(forms.ModelForm):
    class Meta:
        model = ImagemCarrossel
        
        fields = ['imagem', 'legenda', 'ativo', 'praia_link']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'legenda': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto que aparece sobre a imagem'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # O Django criará um <select> (dropdown) automaticamente para o link da praia
            'praia_link': forms.Select(attrs={'class': 'form-select'}),
        }

class ReciboManualForm(forms.Form):
    FORMAS_PAGAMENTO = [
        ('', '-- Selecione --'),
        ('Pix', 'Pix'),
        ('Dinheiro', 'Dinheiro'),
        ('Cartão de Crédito', 'Cartão de Crédito'),
        ('Cartão de Débito', 'Cartão de Débito'),
        ('Transferência Bancária', 'Transferência Bancária'),
    ]

    numero_recibo = forms.CharField(label="Número do Recibo")
    recebemos_de = forms.CharField(label="Recebemos de (Nome do Cliente)")
    servico_prestado = forms.CharField(label="Serviço Prestado", widget=forms.Textarea(attrs={'rows': 3}))
    valor = forms.DecimalField(label="Valor (R$)", max_digits=8, decimal_places=2)
    forma_pagamento = forms.ChoiceField(label="Forma de Pagamento", choices=FORMAS_PAGAMENTO)
    data_viagem = forms.DateField(label="Data da Viagem/Serviço", widget=forms.DateInput(attrs={'type': 'date'}))
    origem = forms.CharField(label="Origem")
    destino = forms.CharField(label="Destino")
    observacoes = forms.CharField(label="Observações (opcional)", widget=forms.Textarea(attrs={'rows': 3}), required=False)
    cnpj_emitente = forms.CharField(label="CNPJ do Emitente", initial='33780923000162')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# dashboard/forms.py
from django import forms # Garanta que 'forms' está importado
# ...

class GuiaForm(forms.ModelForm):
    class Meta:
        model = Guia
        fields = ['nome', 'telefone', 'placa_carro', 'modelo_carro', 'cor_carro', 'ativo']

    # SUBSTITUA O SEU __init__ POR ESTE:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Se o campo for um checkbox, aplica a classe 'form-check-input'
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            # Para todos os outros campos, aplica a classe 'form-control'
            else:
                field.widget.attrs.update({'class': 'form-control'})

class ReservaEditForm(forms.ModelForm):
    class Meta:
        model = Reserva
        # Agora o campo 'guia' existe, então podemos listar ele aqui!
        fields = ['data_agendamento', 'numero_passageiros', 'local_partida', 'local_chegada', 'informacoes_voo', 'guia']
        
        widgets = {
            'data_agendamento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'numero_passageiros': forms.NumberInput(attrs={'class': 'form-control'}),
            'local_partida': forms.TextInput(attrs={'class': 'form-control'}),
            'local_chegada': forms.TextInput(attrs={'class': 'form-control'}),
            'informacoes_voo': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Campo de seleção do Guia
            'guia': forms.Select(attrs={'class': 'form-select'}),
        }
        
        labels = {
            'data_agendamento': 'Nova Data e Hora',
            'numero_passageiros': 'Novo Nº de Passageiros',
            'local_partida': 'Novo Local de Partida',
            'local_chegada': 'Novo Local de Chegada',
            'informacoes_voo': 'Nº do Voo',
            'guia': 'Guia Responsável',
        }

class ReservaManualForm(forms.Form):
    # --- DADOS DO CLIENTE ---
    nome_cliente = forms.CharField(label="Nome", widget=forms.TextInput(attrs={'class': 'form-control'}))
    sobrenome_cliente = forms.CharField(label="Sobrenome", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email_cliente = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefone_cliente = forms.CharField(label="Telefone", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}))

    # --- DADOS DO SERVIÇO ---
    TIPO_SERVICO_CHOICES = (
        ('passeio', 'Passeio'),
        ('transfer', 'Transfer'),
    )
    tipo_servico = forms.ChoiceField(
        label="Tipo de Serviço",
        choices=TIPO_SERVICO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleCampos()'})
    )

    # Campo para escolher a Praia (se for Passeio)
    praia_selecionada = forms.ModelChoiceField(
        queryset=Praia.objects.all(),
        required=False,
        label="Escolha o Passeio",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Campos para Transfer (se for Transfer)
    local_partida = forms.CharField(required=False, label="Local de Partida", widget=forms.TextInput(attrs={'class': 'form-control'}))
    local_chegada = forms.CharField(required=False, label="Local de Chegada", widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Campos Comuns
    data_agendamento = forms.DateTimeField(
        label="Data e Hora",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    numero_passageiros = forms.IntegerField(label="Nº Passageiros", widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))
    valor = forms.DecimalField(label="Valor Combinado (R$)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    informacoes_voo = forms.CharField(required=False, label="Info Voo / Obs", widget=forms.TextInput(attrs={'class': 'form-control'}))

class PraiaForm(forms.ModelForm):
    class Meta:
        model = Praia
        # CORREÇÃO: Usar 'descricao_longa' em vez de 'descricao_completa'
        fields = ['nome', 'descricao_curta', 'descricao_longa', 'imagem', 'valor', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_curta': forms.TextInput(attrs={'class': 'form-control'}),
            # CORREÇÃO AQUI TAMBÉM NO WIDGET:
            'descricao_longa': CKEditorWidget(),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'email', 'telefone'] # Ajuste conforme seu model
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
        }

class DepoimentoForm(forms.ModelForm):
    class Meta:
        model = Depoimento
        fields = ['nome', 'cidade', 'texto', 'foto', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'imagem_destaque', 'status']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da postagem'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Escreva seu artigo aqui...'}),
            'imagem_destaque': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class CarrosselForm(forms.ModelForm):
    class Meta:
        model = ImagemCarrossel
        # O CAMPO 'ativo' PRECISA ESTAR NESTA LISTA PARA APARECER:
        fields = ['imagem', 'titulo', 'legenda', 'ativo', 'praia_link', 'transfer_link'] 
        
        widgets = {
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Bem-vindo a Maragogi'}),
            'legenda': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: O Caribe Brasileiro'}),
            
            # O widget 'form-check-input' é o que dá o visual de "interruptor" (switch)
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            'praia_link': forms.Select(attrs={'class': 'form-select'}),
            'transfer_link': forms.Select(attrs={'class': 'form-select'}),
        }

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        # Certifique-se de que os campos aqui batem com o que você quer preencher
        # NÃO coloque 'slug' aqui se quiser que ele gere automático
        fields = ['titulo', 'origem', 'destino', 'descricao', 'imagem', 'valor', 'direcao', 'mais_vendido'] 
        
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'origem': forms.TextInput(attrs={'class': 'form-control'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'direcao': forms.Select(attrs={'class': 'form-select'}),
            'mais_vendido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BloqueioForm(forms.ModelForm):
    class Meta:
        model = Bloqueio
        fields = ['data', 'praia', 'motivo']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'praia': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Lotado, Feriado...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Deixa o campo praia opcional visualmente ("--- Bloqueio Geral ---")
        self.fields['praia'].empty_label = "--- BLOQUEIO GERAL (TODOS OS PASSEIOS) ---"