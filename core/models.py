from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import random   # <--- NOVO
import string   # <--- NOVO

# =========================================
# 1. NOVO MODELO: CLIENTE
# =========================================
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"

# =========================================
# 2. SEUS MODELOS EXISTENTES
# =========================================

class Praia(models.Model):
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=255)
    descricao_longa = models.TextField() 
    imagem = models.ImageField(upload_to='praias/')
    slug = models.SlugField(unique=True, help_text="URL amigável, ex: praia-do-gunga")
    valor = models.DecimalField(max_digits=7, decimal_places=2, help_text="Valor do passeio por pessoa", default=0.00)
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Transforma "City Tour Maceió" em "city-tour-maceio"
            self.slug = slugify(self.nome) 
        super().save(*args, **kwargs)
    def __str__(self):
        return self.nome

class ImagemCarrossel(models.Model):
    imagem = models.ImageField(upload_to='carrossel/')
    
    # ADICIONE ESTES CAMPOS QUE ESTÃO FALTANDO:
    titulo = models.CharField(max_length=100, blank=True, null=True)
    legenda = models.CharField(max_length=200, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    
    # E ESTES SÃO OS LINKS QUE ADICIONAMOS HOJE:
    praia_link = models.ForeignKey('Praia', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ligar a um Passeio")
    transfer_link = models.ForeignKey('Transfer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ligar a um Transfer")
    
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo or "Imagem Carrossel"
    
class Guia(models.Model):
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True)
    placa_carro = models.CharField("Placa do Carro", max_length=10, blank=True)
    modelo_carro = models.CharField("Modelo do Carro", max_length=50, blank=True)
    cor_carro = models.CharField("Cor do Carro", max_length=30, blank=True)
    ativo = models.BooleanField(default=True, help_text="Marque se o guia está disponível para novos passeios")

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
    slug = models.SlugField(max_length=200, unique=True, help_text="URL amigável gerada a partir do título.")
    origem = models.CharField(max_length=100, help_text="Ex: Aeroporto de Maceió (MCZ)")
    destino = models.CharField(max_length=100, help_text="Ex: Hotéis na Orla (Pajuçara)")
    descricao = models.CharField(max_length=255)
    descricao_longa = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='transfers/')
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    mais_vendido = models.BooleanField(default=False, help_text="Marque esta opção para destacar este transfer como 'Mais Vendido'.")
    direcao = models.CharField(max_length=15, choices=DIRECAO_CHOICES, default='outros')

    def save(self, *args, **kwargs):
        # Se não tiver slug (link), cria um baseado no título
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.titulo

# =========================================
# 3. NOVO MODELO: RESERVA
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

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    praia_destino = models.ForeignKey(Praia, on_delete=models.SET_NULL, null=True, blank=True)
    
    guia = models.ForeignKey(Guia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Guia Responsável")
    # Campo para salvar o nome do transfer ou local
    local_partida = models.CharField(max_length=200, blank=True, null=True)
    local_chegada = models.CharField(max_length=200, blank=True, null=True)
    
    data_agendamento = models.DateTimeField()
    numero_passageiros = models.IntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    informacoes_voo = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva #{self.id} - {self.cliente}"
    
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
    conteudo = models.TextField()
    imagem_destaque = models.ImageField(upload_to='blog/')
    data_publicacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rascunho')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
    
def gerar_codigo_reserva():
    # Gera 6 caracteres (Letras Maiúsculas e Números)
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ... (Mantenha Cliente, Praia, ImagemCarrossel, Guia, Transfer iguais) ...

# =========================================
# 3. MODELO: RESERVA (ATUALIZADO)
# =========================================
class Reserva(models.Model):
    # ... seus choices ...
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

    # --- CAMPO NOVO: CÓDIGO ---
    # unique=True garante que nunca haverá dois iguais
    codigo = models.CharField(max_length=10, default=gerar_codigo_reserva, unique=True, editable=False)
    
    # ... seus campos existentes ...
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    guia = models.ForeignKey(Guia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Guia Responsável")
    praia_destino = models.ForeignKey(Praia, on_delete=models.SET_NULL, null=True, blank=True)
    local_partida = models.CharField(max_length=200, blank=True, null=True)
    local_chegada = models.CharField(max_length=200, blank=True, null=True)
    data_agendamento = models.DateTimeField()
    numero_passageiros = models.IntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    informacoes_voo = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Agora mostramos o Código no painel admin também
        return f"Reserva #{self.codigo} - {self.cliente}"