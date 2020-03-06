from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/login/', views.login_for_angular, name='login'),
    path('accounts/logout/', views.logout_for_angular, name='logout'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/create/', views.create_account, name='create'),
    path('accounts/localization/', views.LocalizationView.as_view(), name='localization'),
    path('accounts/matchs/', views.MatchsView.as_view(), name='matchs'),
    path('books/mine/list/', views.ListMyBooksView.as_view(), name='list_mine_book'),
    path('books/mine/add/', views.AddMyBookView.as_view(), name='create_mine_book'),
    path('books/mine/delete/', views.DeleteMyBookView.as_view(), name='delete_mine_book'),
    path('books/desired/list/', views.ListDesiredBooksView.as_view(), name='list_desired_book'),
    path('books/desired/add/', views.AddDesiredBookView.as_view(), name='create_desired_book'),
    path('books/desired/delete/', views.DeleteDesiredBookView.as_view(), name='delete_desired_book'),
    path('knowledge/mine/list/', views.ListMyKnowledgesView.as_view(), name='list_mine_knowledge'),
    path('knowledge/mine/add/', views.AddMyKnowledgeView.as_view(), name='create_mine_knowledge'),
    path('knowledge/mine/delete/', views.DeleteMyKnowledgeView.as_view(), name='delete_mine_knowledge'),
    path('knowledge/desired/list/', views.ListDesiredKnowledgesView.as_view(), name='list_desired_knowledge'),
    path('knowledge/desired/add/', views.AddDesiredKnowledgeView.as_view(), name='create_desired_knowledge'),
    path('knowledge/desired/delete/', views.DeleteDesiredKnowledgeView.as_view(), name='delete_desired_knowledge'),
    path('chat/messages/', views.ListMessagesView.as_view(), name='list_messages'),
    path('chat/messages/received/', views.ReceivedMessagesView.as_view(), name='received_messages'),
    path('chat/messages/send/', views.SendMessagesView.as_view(), name='send_messages'),
]
