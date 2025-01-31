from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from products import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin Routes
    path('admin-login/', views.admin_login, name="admin_login"),
    path('admin-dashboard/', views.admin_dashboard, name="admin_dashboard"),

    # Vendor & User Dashboards
    path('vendor-dashboard/', views.vendor_dashboard, name="vendor_dashboard"),
    path('user-dashboard/', views.user_dashboard, name="user_dashboard"),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),  # Delete user
    path('delete-vendor/<int:vendor_id>/', views.delete_vendor, name='delete_vendor'),  # Delete shop/vendor
    # Edit and Delete Product Routes
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),  # Fix here
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),  # Fix here
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('', include('products.urls')), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
