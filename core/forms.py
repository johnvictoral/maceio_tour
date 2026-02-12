from django import forms
from .models import Cliente, Reserva,Transfer
from .models import Reserva, Bloqueio # <--- Não esqueça de importar o Bloqueio aqui

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

