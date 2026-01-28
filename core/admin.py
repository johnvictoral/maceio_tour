from django.contrib import admin
from .models import Praia, ImagemCarrossel, Guia, Transfer, Cliente, Reserva

# --- Modelos Antigos ---
admin.site.register(Praia)
admin.site.register(ImagemCarrossel)
admin.site.register(Guia)
admin.site.register(Transfer)

# --- Novos Modelos (Do Dashboard) ---

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sobrenome', 'email', 'telefone', 'data_cadastro')
    search_fields = ('nome', 'email', 'telefone')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'status', 'data_agendamento', 'valor')
    list_filter = ('status', 'tipo', 'data_agendamento')
    search_fields = ('cliente__nome', 'cliente__email')