from django.db import models
from core.models import Praia, Guia
import random
from datetime import datetime

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    # ADICIONE ESTA LINHA
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)

    def __str__(self):
        # Vamos melhorar o __str__ para mostrar o nome completo
        return f"{self.nome} {self.sobrenome}"

