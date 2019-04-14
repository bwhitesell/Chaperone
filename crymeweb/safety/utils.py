from .models import SafetyModel


# Load active models into memory
pc_model = SafetyModel.objects.active_model('PC')
PC_DESCRIPTION = 'The probability of a crime occuring within a half mile of the lat/lon provided in the next hour.'


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    ip = '161.149.146.201' if ip == '127.0.0.1' else ip
    return ip
