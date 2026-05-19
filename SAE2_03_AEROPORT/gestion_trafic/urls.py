from django.urls import path
from . import views

urlpatterns = [
    path('', views.AccueilView.as_view(), name='accueil'),

    # URLs Aéroports
    path('aeroports/', views.AeroportListView.as_view(), name='liste_aeroports'),
    path('aeroports/ajouter/', views.AeroportCreateView.as_view(), name='ajouter_aeroport'),
    path('aeroports/<int:pk>/modifier/', views.AeroportUpdateView.as_view(), name='modifier_aeroport'),
    path('aeroports/<int:pk>/supprimer/', views.AeroportDeleteView.as_view(), name='supprimer_aeroport'),

    # URLs Pistes
    path('pistes/', views.PisteListView.as_view(), name='liste_pistes'),
    path('pistes/ajouter/', views.PisteCreateView.as_view(), name='ajouter_piste'),
    path('pistes/<int:pk>/modifier/', views.PisteUpdateView.as_view(), name='modifier_piste'),
    path('pistes/<int:pk>/supprimer/', views.PisteDeleteView.as_view(), name='supprimer_piste'),

    # URLs Compagnies
    # URLs Compagnies (Correction ici : Compagnie sans 's' aux classes)
    path('compagnies/', views.CompagnieListView.as_view(), name='liste_compagnies'),
    path('compagnies/ajouter/', views.CompagnieCreateView.as_view(), name='ajouter_compagnie'),
    path('compagnies/<int:pk>/modifier/', views.CompagnieUpdateView.as_view(), name='modifier_compagnie'),
    path('compagnies/<int:pk>/supprimer/', views.CompagnieDeleteView.as_view(), name='supprimer_compagnie'),

    # URLs Types d'avions
    path('types-avions/', views.TypeAvionListView.as_view(), name='liste_types_avions'),
    path('types-avions/ajouter/', views.TypeAvionCreateView.as_view(), name='ajouter_type_avion'),
    path('types-avions/<int:pk>/modifier/', views.TypeAvionUpdateView.as_view(), name='modifier_type_avion'),
    path('types-avions/<int:pk>/supprimer/', views.TypeAvionDeleteView.as_view(), name='supprimer_type_avion'),

    # URLs Avions
    path('avions/', views.AvionListView.as_view(), name='liste_avions'),
    path('avions/ajouter/', views.AvionCreateView.as_view(), name='ajouter_avion'),
    path('avions/<int:pk>/modifier/', views.AvionUpdateView.as_view(), name='modifier_avion'),
    path('avions/<int:pk>/supprimer/', views.AvionDeleteView.as_view(), name='supprimer_avion'),

    # URLs Vols
    path('vols/', views.VolListView.as_view(), name='liste_vols'),
    path('vols/ajouter/', views.VolCreateView.as_view(), name='ajouter_vol'),
    path('vols/<int:pk>/modifier/', views.VolUpdateView.as_view(), name='modifier_vol'),
    path('vols/<int:pk>/supprimer/', views.VolDeleteView.as_view(), name='supprimer_vol'),
]