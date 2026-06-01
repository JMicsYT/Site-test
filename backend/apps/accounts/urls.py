from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    AccountUnlockView,
    DashboardView,
    LoginView,
    OrderListView,
    PasswordChangeView,
    ProfileEditView,
    RegisterView,
    ResendVerifyEmailView,
    VerifyEmailView,
    logout_view,
)
from .views_referral import ReferralView
from .views_twofa import (
    TwoFactorDisableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("resend-verify-email/", ResendVerifyEmailView.as_view(), name="resend_verify_email"),
    path("verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify_email"),
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="twofa_setup"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="twofa_disable"),
    path("2fa/verify/", TwoFactorVerifyView.as_view(), name="twofa_verify"),
    path("unlock/<str:token>/", AccountUnlockView.as_view(), name="unlock"),
    path("referral/", ReferralView.as_view(), name="referral"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

