from django.urls import path

from . import views

app_name = "lotto_admin"

urlpatterns = [
    path("", views.index, name="index"),  # 루트로 연결될 기본 페이지
    path("sales/", views.sales_history, name="sales_history"),
    path("draw/", views.draw_lottery, name="draw_lottery"),
    path("winnings/", views.winning_history, name="winning_history"),
]
