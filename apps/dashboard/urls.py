from django.urls import path
from apps.dashboard.views import *

urlpatterns = [
    path("", login_view, name="login_view"),
    path("logout/", logout_view, name="logout_view"),
    path("profile/", profile_view, name="profile_view"),
    path("party/", party_list, name="party_list"),
    path("party/<uuid:pk>/", party_detail, name="party_detail"),
    path("payments/", payment_list, name="payment_list"),
    path("dashboard/", dashboard_view, name="dashboard_view")
]