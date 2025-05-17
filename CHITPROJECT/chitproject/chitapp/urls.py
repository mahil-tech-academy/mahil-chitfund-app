from django.urls import path
from .import views 

urlpatterns = [
    path('register/', views.register, name='register'),
    path('make_admin/', views.make_admin, name='make_admin'),
    path('remove_admin/', views.remove_admin, name='remove_admin'),
    path('admin_login/', views.admin_login, name='admin_login'),
     path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('Login/', views.login_redirect),
    path('index/', views.index, name='index'),
    path('logout',views.logout_page,name='logout'),
    path('register_chit/', views.register_chit, name='register_chit'),
    path('success/', views.success, name='success'),
    path('view_chits/', views.view_chits, name='view_chits'),
    path('edit_chit/<int:chit_id>/', views.edit_chit, name='edit_chit'),
    path('handle_payment/<int:chit_id>/', views.handle_payment, name='handle_payment'),
    path('payment_summary/<int:chit_id>/', views.payment_summary, name='payment_summary'),
    path('summary_page/', views.summary_page, name='summary_page'),
    path('admin_config_view/', views.admin_config_view, name='admin_config'),
    path("config_view/", views.config_view, name="config_view"),
    path("pending_week/",views.pending_week,name="pending_week"),
    path('chit_payment/<int:chit_id>/', views.chit_payment_detail, name='chit_payment_detail'),
]
