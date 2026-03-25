from django.urls import path
from . import views # The '.' tells Django to look in the current folder
from django.contrib.auth import views as auth_views # This is the missing piece!

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/complete/<int:pk>/', views.complete_task, name='complete_task'),
    path('tasks/delete/<int:pk>/', views.delete_task, name='delete_task'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('subtasks/', views.subtask_list, name='subtask_list'),
    path('categories/', views.category_list, name='category_list'),
    path('priorities/', views.priority_list, name='priority_list'),
    path('notes/', views.note_list, name='note_list'),
    
    # Task update
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    
    # SubTasks
    path('subtasks/create/', views.SubTaskCreateView.as_view(), name='subtask_create'),
    path('subtasks/<int:pk>/edit/', views.SubTaskUpdateView.as_view(), name='subtask_update'),
    path('subtasks/<int:pk>/delete/', views.SubTaskDeleteView.as_view(), name='subtask_delete'),

    # Categories
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Priorities
    path('priorities/create/', views.PriorityCreateView.as_view(), name='priority_create'),
    path('priorities/<int:pk>/edit/', views.PriorityUpdateView.as_view(), name='priority_update'),
    path('priorities/<int:pk>/delete/', views.PriorityDeleteView.as_view(), name='priority_delete'),

    # Notes
    path('notes/create/', views.NoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/edit/', views.NoteUpdateView.as_view(), name='note_update'),
    path('notes/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note_delete'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]