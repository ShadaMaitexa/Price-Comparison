from django import forms
from django.contrib.auth.models import User
from .models import UserType, VendorProfile, Product, Category

class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    user_type = forms.ChoiceField(choices=UserType.TYPE_CHOICES, widget=forms.Select())
    
    shop_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'user_type', 'shop_name', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add class to each field to match CSS
        self.fields['username'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Enter your username'})
        self.fields['email'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Enter your email'})
        self.fields['password'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Create a password'})
        self.fields['confirm_password'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Confirm your password'})
        self.fields['user_type'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Select your user type'})
        self.fields['shop_name'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Enter your shop name (if applicable)'})
        self.fields['phone'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Enter your phone number'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            
            user_type = UserType.objects.create(user=user, user_type=self.cleaned_data["user_type"])

            # Check if user is a vendor and shop name is unique
            if user_type.user_type == "vendor":
                shop_name = self.cleaned_data["shop_name"]
                # Ensure shop name is unique
                if VendorProfile.objects.filter(shop_name=shop_name).exists():
                    raise forms.ValidationError(f"Shop name '{shop_name}' is already taken. Please choose a different one.")

                # Create VendorProfile
                VendorProfile.objects.create(user=user, shop_name=shop_name, phone=self.cleaned_data["phone"])

        return user

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Select Category", required=True)

    class Meta:
        model = Product
        fields = ['name', 'price', 'quantity', 'image', 'description', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add class and placeholder to product fields
        self.fields['name'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Product name'})
        self.fields['price'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Product price'})
        self.fields['quantity'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Quantity'})
        self.fields['image'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Upload product image'})
        self.fields['description'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Product description'})
        self.fields['category'].widget.attrs.update({'class': 'input-field', 'placeholder': 'Select category'})

