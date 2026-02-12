from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.http import HttpResponse

# --- BIBLIOTECAS PARA O PDF ---
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Importando seus modelos (Adicionei Bloqueio aqui)
from .models import Praia, ImagemCarrossel, Guia, Transfer, Cliente, Reserva, Post, Depoimento, Bloqueio

# =======================================================
# 1. FUNÇÃO QUE DESENHA O VOUCHER PDF
# =======================================================
def gerar_voucher_pdf(reserva):
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
    
    # --- TÍTULO DO DOCUMENTO ---
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, 720, f"VOUCHER DE CONFIRMAÇÃO #{reserva.codigo}")
    
    # --- DADOS DO CLIENTE ---
    y = 680
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "DADOS DO CLIENTE")
    y -= 25
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Nome: {reserva.cliente.nome} {reserva.cliente.sobrenome}")
    y -= 20
    p.drawString(50, y, f"Email: {reserva.cliente.email}")
    y -= 20
    p.drawString(50, y, f"Telefone: {reserva.cliente.telefone}")
    
    # --- DETALHES DA RESERVA ---
    y -= 40
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
    y -= 20
    
    data_formatada = reserva.data_agendamento.strftime('%d/%m/%Y às %H:%M')
    p.drawString(50, y, f"Data: {data_formatada}")
    y -= 20
    p.drawString(50, y, f"Passageiros: {reserva.numero_passageiros}")
    
    if reserva.local_partida:
        y -= 20
        p.drawString(50, y, f"Local de Saída: {reserva.local_partida}")

    # --- DADOS DO GUIA/MOTORISTA (SE TIVER) ---
    if reserva.guia:
        y -= 50
        p.setFillColor(colors.aliceblue)
        p.rect(40, y-80, 515, 95, fill=1, stroke=0)
        
        p.setFillColor(colors.darkblue)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "SEU MOTORISTA / GUIA")
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, f"Nome: {reserva.guia.nome}")
        y -= 20
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Veículo: {reserva.guia.modelo_carro} - {reserva.guia.cor_carro}")
        p.drawString(300, y, f"Placa: {reserva.guia.placa_carro}")
        y -= 20
        p.drawString(50, y, f"Telefone: {reserva.guia.telefone}")
        
        p.setFillColor(colors.black)

    # --- RODAPÉ ---
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, 100, "Apresente este voucher ao motorista no momento do embarque.")
    p.drawCentredString(width/2, 85, "Obrigado por escolher a Vá com John Turismo!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

# =======================================================
# 2. CONFIGURAÇÃO DOS ADMINS (DASHBOARD)
# =======================================================

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    # CORREÇÃO: 'status' precisa estar aqui para o list_editable funcionar
    list_display = ('codigo', 'cliente', 'tipo', 'status', 'data_agendamento', 'valor', 'guia')
    list_filter = ('status', 'tipo', 'data_agendamento')
    search_fields = ('cliente__nome', 'cliente__email', 'codigo')
    list_editable = ('status', 'guia') 
    readonly_fields = ('codigo',)

    def save_model(self, request, obj, form, change):
        if change:
            virou_confirmado = 'status' in form.changed_data and obj.status == 'confirmado'
            mudou_guia = 'guia' in form.changed_data and obj.status == 'confirmado'
            
            if virou_confirmado or mudou_guia:
                try:
                    servico_nome = obj.praia_destino.nome if obj.praia_destino else (obj.local_chegada or "Transfer")
                    
                    try:
                        html_content = render_to_string('core/emails/reserva_confirmada.html', {
                            'nome_cliente': obj.cliente.nome,
                            'codigo': obj.codigo,
                            'data_viagem': obj.data_agendamento,
                            'servico': servico_nome,
                            'guia': obj.guia,
                        })
                    except Exception:
                        html_content = f"<p>Sua reserva <b>#{obj.codigo}</b> foi confirmada!</p>"
                    
                    text_content = strip_tags(html_content)
                    pdf_buffer = gerar_voucher_pdf(obj)
                    filename = f"Voucher_{obj.codigo}.pdf"

                    email = EmailMultiAlternatives(
                        subject=f'Reserva CONFIRMADA + Voucher #{obj.codigo}',
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[obj.cliente.email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
                    email.send()
                    
                    self.message_user(request, f"✅ E-mail enviado com Voucher PDF para {obj.cliente.nome}!", level='SUCCESS')
                except Exception as e:
                    self.message_user(request, f"⚠️ Reserva salva, mas erro no envio do e-mail: {e}", level='WARNING')

        super().save_model(request, obj, form, change)

# --- ADICIONEI O ADMIN DO BLOQUEIO AQUI ---
@admin.register(Bloqueio)
class BloqueioAdmin(admin.ModelAdmin):
    list_display = ('data', 'tipo_bloqueio', 'motivo')
    list_filter = ('data', 'praia')
    date_hierarchy = 'data'
    
    def tipo_bloqueio(self, obj):
        if obj.praia:
            return f"🚫 Apenas: {obj.praia.nome}"
        return "⛔ BLOQUEIO TOTAL (Site Inteiro)"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sobrenome', 'email', 'telefone', 'data_cadastro')
    search_fields = ('nome', 'email', 'telefone')

# --- Outros Modelos ---
admin.site.register(Praia)
admin.site.register(ImagemCarrossel)
admin.site.register(Guia)
admin.site.register(Transfer)
admin.site.register(Post)
admin.site.register(Depoimento)