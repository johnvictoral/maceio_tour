from django import forms
from core.models import Reserva, Cliente
from core.models import Post

# --- FORMULÁRIO DE CLIENTE (Usado em vários lugares) ---
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'email', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
        }

# --- FORMULÁRIO PARA RESERVA DE PASSEIO (quando o cliente está na página de uma praia) ---
class ReservaPasseioForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['data_agendamento', 'numero_passageiros', 'local_partida']
        widgets = {
            'data_agendamento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'numero_passageiros': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'local_partida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Hotel ou Pousada'}),
        }
        labels = {
            'data_agendamento': 'Escolha a Data e Hora do Passeio',
            'numero_passageiros': 'Quantidade de Pessoas',
            'local_partida': 'Onde devemos buscar você? (Local de Partida)',
        }

# --- FORMULÁRIO PARA RESERVA DE TRANSFER ESPECÍFICO (quando o cliente está na página de um transfer) ---
# Este é o novo formulário simples.
class ReservaTransferForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['data_agendamento', 'numero_passageiros', 'informacoes_voo']
        widgets = {
            'data_agendamento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'numero_passageiros': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'informacoes_voo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional. Ex: GOL G3 1234'}),
        }
        labels = {
            'data_agendamento': 'Data e Hora de Partida do Transfer',
            'numero_passageiros': 'Quantidade de Passageiros',
            'informacoes_voo': 'Companhia Aérea e Número do Voo (se aplicável)',
        }

# --- FORMULÁRIO PARA COTAÇÃO DE TRANSFER GENÉRICO (o antigo, que pede origem e destino) ---
# Vamos mantê-lo para uso futuro.
class SolicitarTransferForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['local_partida', 'local_chegada', 'data_agendamento', 'numero_passageiros', 'informacoes_voo']
        # (os widgets e labels deste formulário podem ser adicionados aqui se necessário no futuro)

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