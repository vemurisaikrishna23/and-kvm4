from django.contrib import admin
from . import models

# Loop through all models in this app and register them
for model_name in dir(models):
    model = getattr(models, model_name)
    try:
        if issubclass(model, models.models.Model):
            admin.site.register(model)
    except Exception:
        pass
