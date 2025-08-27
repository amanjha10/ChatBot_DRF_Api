from django.urls import path
from . import views

urlpatterns = [
    # User Profile Management (Admin/SuperAdmin only)
    path('user-profiles/', views.user_profiles_list_view, name='user_profiles_list'),
    path('user-profiles/<int:profile_id>/', views.user_profile_detail_view, name='user_profile_detail'),
    path('user-profiles/stats/', views.user_profiles_stats_view, name='user_profiles_stats'),
    path('user-profiles/<int:profile_id>/delete/', views.delete_user_profile_view, name='delete_user_profile'),
    
    # Agent Management (Admin/SuperAdmin only)
    path('create-agent/', views.create_agent_view, name='create_agent'),
    path('list-agents/', views.list_agents_view, name='list_agents'),
    path('update-agent/<int:agent_id>/', views.update_agent_view, name='update_agent'),
    path('reset-agent-password/', views.reset_agent_password_view, name='reset_agent_password'),
    
    # Agent Authentication
    path('agent-first-login/', views.agent_first_login_view, name='agent_first_login'),
    path('agent-login/', views.agent_login_view, name='agent_login'),
    path('agent-logout/', views.agent_logout_view, name='agent_logout'),
    
    # Agent Status Management
    path('update-agent-status/', views.update_agent_status_view, name='update_agent_status'),
    
    # Agent Sessions (Analytics)
    path('agent-sessions/', views.agent_sessions_view, name='agent_sessions'),

    # Debug (temporary)
    path('debug-agent/<int:agent_id>/', views.debug_agent_view, name='debug_agent'),
]
