import pickle
import os
from django.conf import settings


MODEL_PATH = os.path.join(settings.BASE_DIR,'hospital','mlmodels','classifier.pkl')

def load_model():
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        return model
    return false