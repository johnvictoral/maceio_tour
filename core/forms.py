from django import forms
from .models import Cliente, Reserva,Transfer

class ClientePublicoForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'email', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu primeiro nome'}),
            'sobrenome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@email.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
        }

class ReservaPublicaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['data_agendamento', 'numero_passageiros', 'local_partida', 'informacoes_voo']
        widgets = {
            'data_agendamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_passageiros': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'local_partida': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qual hotel você estará?'}),
            'informacoes_voo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional: Nº do Voo / Horário'}),
        }

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['titulo', 'descricao', 'valor', 'imagem', 'direcao'] 
        # Ajuste os campos conforme seu model. Ex: 'direcao' (ida, volta, etc)
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'direcao': forms.Select(attrs={'class': 'form-select'}),
        }

