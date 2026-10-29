from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.home_view, name='dashboard'),

    path('tasks/', views.task_list_view, name='task_list'),
    path('tasks/<slug:slug>/', views.task_detail_view, name='task_detail'),

    path('courses/', views.courses_list_view, name='courses_list'),
    path('courses/<slug:slug>/', views.course_detail_view, name='course_detail'),
    path('courses/<slug:course_slug>/<slug:lesson_slug>/', views.lesson_detail_view, name='lesson_detail'),

    path('playground/', views.playground_view, name='playground'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('demo-login/', views.quick_demo_login, name='demo_login'),

    path('api/run-code/', views.run_code_api, name='api_run_code'),
    path('api/tasks/<slug:slug>/submit/', views.submit_task_api, name='api_submit_task'),
]
