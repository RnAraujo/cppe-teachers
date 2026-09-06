from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/teacher/add/', views.add_teacher, name='add_teacher'),
    path('dashboard/teacher/<int:teacher_id>/edit/', views.edit_teacher, name='edit_teacher'),
    path('dashboard/teacher/<int:teacher_id>/contributions/', views.teacher_contributions, name='teacher_contributions'),
    path('dashboard/teacher/<int:teacher_id>/contribution/', views.add_contribution, name='add_contribution'),
    path('dashboard/receipt/<int:contribution_id>/', views.download_receipt, name='download_receipt'),
    path('dashboard/receipts/download/', views.download_receipts, name='download_receipts'),
]