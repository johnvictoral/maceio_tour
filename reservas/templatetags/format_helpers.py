# reservas/templatetags/format_helpers.py

from django import template
import re

register = template.Library()

@register.filter
def format_whatsapp_number(value):
    if not value:
        return ""
    # Remove todos os caracteres que não são números
    cleaned_number = re.sub(r'\D', '', value)

    # Adiciona o código do país (55) se não estiver presente
    if len(cleaned_number) <= 11 and not cleaned_number.startswith('55'):
        cleaned_number = f'55{cleaned_number}'

    return cleaned_number