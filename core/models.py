from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import random
import string
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from ckeditor.fields import RichTextField  # Importante para o Editor de Texto

# =========================================
# 0. FUNÇÕES AUXILIARES
# =========================================
def gerar_codigo_reserva():
    # Gera 6 caracteres (Letras Maiúsculas e Números) ex: A4X9B2
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# =========================================
# 1. MODELO: PARCEIRO (NOVO)
# =========================================
class Parceiro(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parceiro')
    telefone = models.CharField(max_length=20)
    chave_pix = models.CharField(max_length=100, blank=True, null=True, help_text="Chave Pix para receber comissões")
    comissao_padrao = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Porcentagem padrão (%)")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario.first_name} ({self.usuario.email})"

# =========================================
# 2. MODELOS BÁSICOS (CLIENTE, GUIA, ETC)
# =========================================
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"

class Guia(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True)
    placa_carro = models.CharField("Placa do Carro", max_length=10, blank=True)
    modelo_carro = models.CharField("Modelo do Carro", max_length=50, blank=True)
    cor_carro = models.CharField("Cor do Carro", max_length=30, blank=True)
    ativo = models.BooleanField(default=True, help_text="Marque se o guia está disponível para novos passeios")

    def __str__(self):
        return self.nome

class Praia(models.Model):
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=255)
    descricao_longa = RichTextField("Descrição Completa", blank=True, null=True) # CKEditor
    imagem = models.ImageField(upload_to='praias/')
    slug = models.SlugField(unique=True, help_text="URL amigável, ex: praia-do-gunga")
    valor = models.DecimalField(max_digits=7, decimal_places=2, help_text="Valor do passeio por pessoa", default=0.00)
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome) 
        super().save(*args, **kwargs)
    def __str__(self):
        return self.nome

class Transfer(models.Model):
    DIRECAO_CHOICES = (
        ('ida', 'Ida (Aeroporto -> Maceió)'),
        ('volta', 'Volta (Maceió -> Aeroporto)'),
        ('ida_e_volta', 'Ida e Volta'),
        ('outros', 'Outros'),
    )
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    origem = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    descricao = models.CharField(max_length=255)
    descricao_longa = RichTextField(blank=True, null=True) # Pode usar CKEditor aqui também se quiser
    imagem = models.ImageField(upload_to='transfers/')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    mais_vendido = models.BooleanField(default=False)
    direcao = models.CharField(max_length=15, choices=DIRECAO_CHOICES, default='outros')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.titulo

class ImagemCarrossel(models.Model):
    imagem = models.ImageField(upload_to='carrossel/')
    titulo = models.CharField(max_length=100, blank=True, null=True)
    legenda = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    praia_link = models.ForeignKey('Praia', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ligar a um Passeio")
    transfer_link = models.ForeignKey('Transfer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ligar a um Transfer")
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo or "Imagem Carrossel"

class Depoimento(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100, help_text="Ex: São Paulo - SP")
    texto = models.TextField()
    foto = models.ImageField(upload_to='depoimentos/', blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Post(models.Model):
    STATUS_CHOICES = (
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
    )
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    conteudo = RichTextField() # CKEditor no Blog é essencial
    imagem_destaque = models.ImageField(upload_to='blog/')
    data_publicacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rascunho')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.titulo

class Bloqueio(models.Model):
    data = models.DateField("Data Bloqueada")
    praia = models.ForeignKey(Praia, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Passeio Específico")
    motivo = models.CharField(max_length=100, default="Vagas Esgotadas")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        tipo = self.praia.nome if self.praia else "GERAL"
        return f"{self.data} - {tipo}"

    class Meta:
        ordering = ['-data']
        unique_together = ['data', 'praia']

# =========================================
# 3. MODELO PRINCIPAL: RESERVA (UNIFICADO)
# =========================================
class Reserva(models.Model):
    TIPO_CHOICES = (
        ('passeio', 'Passeio'),
        ('transfer', 'Transfer'),
    )
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    )
    
    # 1. Código da Reserva (Gerado Automaticamente)
    codigo = models.CharField(max_length=10, default=gerar_codigo_reserva, unique=True, editable=False)
    
    # 2. Dados Básicos
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    praia_destino = models.ForeignKey(Praia, on_delete=models.SET_NULL, null=True, blank=True)
    guia = models.ForeignKey(Guia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Guia Responsável")
    
    # 3. Detalhes
    local_partida = models.CharField(max_length=200, blank=True, null=True)
    local_chegada = models.CharField(max_length=200, blank=True, null=True)
    data_agendamento = models.DateTimeField()
    numero_passageiros = models.IntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    informacoes_voo = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # 4. NOVOS CAMPOS: PARCEIRO & COMISSÃO
    parceiro = models.ForeignKey(Parceiro, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Comissão do Parceiro")
    status_pagamento_comissao = models.CharField(
        max_length=20,
        choices=[('pendente', 'Pendente'), ('pago', 'Pago')],
        default='pendente'
    )

    def save(self, *args, **kwargs):
        # A. Garante que tem código
        if not self.codigo:
            self.codigo = gerar_codigo_reserva()
            
        # B. Calcula Comissão Automática (Se tiver parceiro e comissão for zero)
        if self.parceiro and self.valor_comissao == 0 and self.valor > 0:
            porcentagem = self.parceiro.comissao_padrao
            self.valor_comissao = (self.valor * porcentagem) / 100
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva #{self.codigo} - {self.cliente}"

# =========================================
# 4. SINAIS (SIGNALS)
# =========================================
@receiver(post_save, sender=User)
def criar_perfil_parceiro(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        Parceiro.objects.get_or_create(usuario=instance)