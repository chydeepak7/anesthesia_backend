from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('categories/', views.DrugCategoryListView.as_view(), name='drug-categories'),
    path('drugs/', views.DrugListView.as_view(), name='drug-list'),
    path('drugs/<int:pk>/', views.DrugDetailView.as_view(), name='drug-detail'),
    path('calculate/', views.DosageCalculatorView.as_view(), name='dosage-calculator'),
]
