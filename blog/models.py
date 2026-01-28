
# Create your models here.
# blog/models.py

from django.db import models
from django.conf import settings # Para pegar o usuário logado

class Post(models.Model):
    STATUS_CHOICES = (
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
    )

    titulo = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="URL amigável, ex: dicas-de-restaurantes-em-maceio")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    conteudo = models.TextField()
    imagem_destaque = models.ImageField(upload_to='blog_images/', help_text="Imagem principal que aparecerá no topo do post e nos cards.")
    data_publicacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rascunho')

    class Meta:
        ordering = ['-data_publicacao'] # Ordena os posts do mais novo para o mais antigo

    def __str__(self):
        return self.titulo