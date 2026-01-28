# blog/views.py

from django.shortcuts import render, get_object_or_404
from .models import Post

# View para a página que lista todos os posts
def lista_de_posts(request):
    # Busca todos os posts com status 'publicado'
    posts_publicados = Post.objects.filter(status='publicado')

    # Pega o post mais recente para ser o destaque
    post_destaque = posts_publicados.first()

    # Pega os outros posts (todos, exceto o primeiro)
    outros_posts = posts_publicados[1:]

    context = {
        'post_destaque': post_destaque,
        'outros_posts': outros_posts,
    }
    return render(request, 'blog/lista_de_posts.html', context)

# View para a página que mostra um post individual
def detalhe_do_post(request, slug):
    # Busca o post pelo 'slug' ou retorna um erro 404 se não encontrar
    post = get_object_or_404(Post, slug=slug, status='publicado')
    context = {
        'post': post
    }
    return render(request, 'blog/detalhe_do_post.html', context)