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

# Importando seus modelos (adicionei Post e Depoimento caso queira usar)
from .models import Praia, ImagemCarrossel, Guia, Transfer, Cliente, Reserva, Post, Depoimento

# =======================================================
# 1. FUNÇÃO QUE DESENHA O VOUCHER PDF
# =======================================================
def gerar_voucher_pdf(reserva):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- CABEÇALHO ---
    p.setFillColor(colors.darkgreen) # Cor da marca
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, 800, "VÁ COM JOHN TURISMO")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, "Maceió - Alagoas | CNPJ: JVC Turismo")
    p.drawString(50, 765, "WhatsApp: (82) 99932-5548")
    
    p.line(50, 750, 550, 750) # Linha horizontal
    
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
    
    # Descobre o nome do serviço
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
        # Desenha um retângulo azul claro de fundo
        p.setFillColor(colors.aliceblue)
        p.rect(40, y-80, 515, 95, fill=1, stroke=0)
        
        p.setFillColor(colors.darkblue) # Texto azul escuro
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
        
        p.setFillColor(colors.black) # Volta pra preto

    # --- RODAPÉ ---
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, 100, "Apresente este voucher ao motorista no momento do embarque.")
    p.drawCentredString(width/2, 85, "Obrigado por escolher a Vá com John Turismo!")
    
    # Fecha e salva o PDF na memória
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

# =======================================================
# 2. CONFIGURAÇÃO DOS ADMINS (DASHBOARD)
# =======================================================

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'cliente', 'tipo', 'status_colorido', 'data_agendamento', 'valor', 'guia')
    list_filter = ('status', 'tipo', 'data_agendamento')
    search_fields = ('cliente__nome', 'cliente__email', 'codigo')
    list_editable = ('status', 'guia') # Permite editar direto na lista!
    readonly_fields = ('codigo',) # Código não pode ser alterado manualmente
    
    # Função para colorir o status na lista (Visual bonito)
    def status_colorido(self, obj):
        from django.utils.html import format_html
        cores = {
            'pendente': 'orange',
            'confirmado': 'green',
            'concluido': 'blue',
            'cancelado': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            cores.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colorido.short_description = 'Status'

    # --- AQUI ACONTECE A MÁGICA DO E-MAIL + PDF ---
    def save_model(self, request, obj, form, change):
        # Verifica se é uma edição (não criação nova)
        if change:
            # Lógica: Se mudou pra Confirmado OU se alterou o Guia numa reserva já confirmada
            virou_confirmado = 'status' in form.changed_data and obj.status == 'confirmado'
            mudou_guia = 'guia' in form.changed_data and obj.status == 'confirmado'
            
            if virou_confirmado or mudou_guia:
                print(f"--- GERANDO VOUCHER E ENVIANDO E-MAIL PARA {obj.cliente.email} ---")
                try:
                    # 1. Prepara o conteúdo do e-mail
                    servico_nome = obj.praia_destino.nome if obj.praia_destino else (obj.local_chegada or "Transfer")
                    
                    # Tenta renderizar o HTML bonito, se não der, vai texto simples
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
                    
                    # 2. Gera o PDF do Voucher
                    pdf_buffer = gerar_voucher_pdf(obj)
                    filename = f"Voucher_{obj.codigo}.pdf"

                    # 3. Cria o e-mail com anexo
                    email = EmailMultiAlternatives(
                        subject=f'Reserva CONFIRMADA + Voucher #{obj.codigo}',
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[obj.cliente.email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    
                    # ANEXA O PDF AQUI
                    email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
                    
                    # Envia
                    email.send()
                    
                    self.message_user(request, f"✅ E-mail enviado com Voucher PDF para {obj.cliente.nome}!", level='SUCCESS')
                except Exception as e:
                    self.message_user(request, f"⚠️ Reserva salva, mas erro no envio do e-mail: {e}", level='WARNING')
                    print(f"ERRO PDF/EMAIL: {e}")

        # Salva no banco de dados
        super().save_model(request, obj, form, change)

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