from django.db import models

class Members(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)

class Ordendj(models.Model):
    ordenv = models.CharField(max_length=255)
    nom_var = models.CharField(max_length=255)
    sentido = models.CharField(max_length=255)

COLOR_CHOICES = (
    ('green','GREEN'),
    ('blue', 'BLUE'),
    ('red','RED'),
    ('orange','ORANGE'),
    ('black','BLACK'),
)

class MyModel(models.Model):
  color = models.CharField(max_length=6, choices=COLOR_CHOICES, default='green')

