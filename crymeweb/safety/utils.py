from .models import SafetyModel


# Load active models into memory
try:
    pc_model = SafetyModel.objects.active_model('PC')
except:
    pc_model = None

PC_DESCRIPTION = 'The probability of a crime occuring within a half mile of the lat/lon provided in the next hour.'

qt_mile_lon = 0.007254180000003885 / 2
qt_mile_lat = 0.008726950000000073 / 2


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    ip = '161.149.146.201' if ip == '127.0.0.1' else ip
    return ip
