from django.contrib.auth.models import User  # Import default User model
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    vendor = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

# Define user types
class UserType(models.Model):
    TYPE_CHOICES = [
        ('user', 'User'),
        ('vendor', 'Vendor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to built-in User model
    user_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='user')

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

# Vendor Model (Only for shop vendors)
class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to User model
    shop_name = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.shop_name
class Notification(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # You can use this later to mark notifications as seen

    def __str__(self):
        return self.message