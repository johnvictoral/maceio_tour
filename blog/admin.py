# Register your models here.
# blog/admin.py

from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'status', 'data_publicacao')
    list_filter = ('status', 'data_publicacao', 'autor')
    search_fields = ('titulo', 'conteudo')
    prepopulated_fields = {'slug': ('titulo',)} # O slug é preenchido automaticamente a partir do título