from django.conf import settings
from .utils import es_admin, es_cliente

def whatsapp_config(request):
    """
    Context processor to make the WhatsApp number available in all templates.
    """
    return {
        'whatsapp_number': getattr(settings, 'WHATSAPP_NUMBER', '573014717412')
    }

def user_status(request):
    """
    Context processor to make es_admin and es_cliente available in all templates.
    """
    if request.user.is_authenticated:
        return {
            'es_admin': es_admin(request.user),
            'es_cliente': es_cliente(request.user)
        }
    return {
        'es_admin': False,
        'es_cliente': False
    }
