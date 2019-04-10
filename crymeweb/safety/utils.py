from datetime import datetime
from .models import SafetyModel
import numpy as np


# Load active models into memory
#pc_model = SafetyModel.objects.active_model('PC')
pc_model =5
PC_DESCRIPTION = 'The probability of a crime occuring within a half mile of the lat/lon provided in the next hour.'
