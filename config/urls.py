from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # O Core cuida do Site e do Blog agora
    path('', include('core.urls')),
    
    # O Dashboard cuida de toda a administração
    path('dashboard/', include('dashboard.urls')),
    
    # REMOVI A LINHA 'reservas/' PARA EVITAR CONFLITOS COM O SISTEMA NOVO
    
    # Rota para Login
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    
    # Rota para Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)