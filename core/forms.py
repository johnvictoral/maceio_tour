from django import forms
from .models import Cliente, Reserva,Transfer
from .models import Reserva, Bloqueio
from .models import Parceiro, Reserva, Cliente

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

    # --- VALIDAÇÃO DE BLOQUEIO DE AGENDA ---
    def clean_data_agendamento(self):
        data_escolhida = self.cleaned_data.get('data_agendamento')

        if data_escolhida:
            # Verifica se existe BLOQUEIO GERAL (praia__isnull=True) para esta data
            # Como o input é type='date', o Python já entende como uma data (dia/mês/ano)
            
            # Se encontrar um bloqueio geral para esse dia, trava o formulário
            if Bloqueio.objects.filter(data=data_escolhida, praia__isnull=True).exists():
                raise forms.ValidationError("Desculpe, nossa agenda está lotada ou indisponível para esta data. Por favor, escolha outro dia.")

        return data_escolhida

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

# --- FORMULÁRIO DE CADASTRO DE PARCEIRO ---
class CadastroParceiroForm(forms.Form):
    nome_completo = forms.CharField(label="Nome Completo", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome ou nome da empresa'}))
    email = forms.EmailField(label="E-mail (Login)", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Será usado para entrar no sistema'}))
    telefone = forms.CharField(label="WhatsApp / Telefone", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(82) 99999-9999'}))
    # REMOVIDO: chave_pix = ...
    senha = forms.CharField(label="Crie uma Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirmar_senha = forms.CharField(label="Confirme a Senha", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error('confirmar_senha', "As senhas não conferem.")
