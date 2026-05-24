# lotto/user/urls.py
from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('', views.index, name='index'),  # 루트로 연결될 기본 페이지
    path('purchase/', views.purchase, name='purchase'),
    path('purchase/success/<int:purchase_id>/', views.purchase_success, name='purchase_success'),
    path('check/', views.check, name='check'),          # 나중에 구현
]