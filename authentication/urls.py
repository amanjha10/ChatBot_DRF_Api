from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.profile_view, name='profile'),

    # Admin Management endpoints (SuperAdmin only)
    path('create-admin/', views.create_admin_view, name='create_admin'),
    path('list-admins/', views.list_admins_view, name='list_admins'),
    path('update-admin/<int:admin_id>/', views.update_admin_view, name='update_admin'),
    path('delete-admin/<int:admin_id>/', views.delete_admin_view, name='delete_admin'),
    path('change-admin-plan/<int:admin_id>/', views.change_admin_plan_view, name='change_admin_plan'),

    # Plan Management endpoints (SuperAdmin only)
    path('create-plan/', views.create_plan_view, name='create_plan'),
    path('list-plans/', views.list_plans_view, name='list_plans'),
    path('list-user-plan-assignments/', views.list_user_plan_assignments_view, name='list_user_plan_assignments'),

    # Subscription Management endpoints (SuperAdmin only)
    path('cancel-subscription/', views.cancel_subscription_view, name='cancel_subscription'),
    path('renew-subscription/', views.renew_subscription_view, name='renew_subscription'),
    path('upgrade-plan/', views.upgrade_plan_view, name='upgrade_plan'),
]
