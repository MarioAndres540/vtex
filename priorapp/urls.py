from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('priorapp/', views.priorapp, name='priorapp'),
    path('cargar/', views.cargar, name='cargar'),
    path('priorizar/', views.priorizar, name='priorizar'),
    path('priorizar/add/', views.add, name='add'),
    path('priorizar/add/addrecord/', views.addrecord, name='addrecord'),
    path('priorizar/delete/<int:id>', views.delete, name='delete'),
    path('priorizar/update/<int:id>', views.update, name='update'),
    path('priorizar/update/updaterecord/<int:id>', views.updaterecord, name='updaterecord'),
    path('priorizar/deleteord/<int:id>', views.deleteord, name='deleteord'),
    path('priorizar/sentido/<int:id>', views.sentido, name='sentido'),
    path('priorizar/nomvar/<str:id1>/<str:id2>', views.nomvar, name='nomvar'),
    path('verop/', views.verop, name='verop'),
    path('verou/<str:id1>', views.verou, name='verou'),
    path('priorizar/veroq/', views.veroq, name='veroq'),
    path('priorizar/addord/', views.addord, name='addord'),
    path('priorizar/ordup/<int:id>', views.ordup, name='ordup'),
    path('priorizar/orddn/<int:id>', views.orddn, name='orddn'),
    path('priorizar/genvit/', views.genvit, name='genvit'),
    path('verop2/', views.verop2, name='verop2'),
]
