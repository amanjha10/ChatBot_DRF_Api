# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Chat endpoints
    path('chat/', views.chat_message_view, name='chat_message'),
    path('upload/', views.file_upload_view, name='file_upload'),
    path('session-status/', views.session_status_view, name='session_status'),
    
    # Profile management
    path('create-profile/', views.create_profile_view, name='create_profile'),
    path('validate-phone/', views.validate_phone_view, name='validate_phone'),
    path('country-codes/', views.country_codes_view, name='country_codes'),
    
    # RAG system
    path('load-rag-documents/', views.load_rag_documents_view, name='load_rag_documents'),
]
