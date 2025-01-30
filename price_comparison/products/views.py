from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm,ProductForm
from .models import UserType, VendorProfile,Product,Category
from django.contrib.auth.models import User

# Fixed Admin Credentials
ADMIN_USERNAME = "admin123"
ADMIN_PASSWORD = "admin123"

# Home Page
def index(request):
    return render(request, 'products/index.html')

#  User & Vendor Registration
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Check if user already exists
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose another one.")
                return redirect('register')

            # Save user but don't commit to the database yet
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()  # Now save the user object to the database

            # Create UserType for this user
            user_type = UserType.objects.create(user=user, user_type=form.cleaned_data['user_type'])

            # If the user is a vendor, we need to check for the shop name and create a VendorProfile
            if user_type.user_type == "vendor":
                shop_name = form.cleaned_data.get("shop_name")
                if not shop_name:
                    messages.error(request, "Shop Name is required for vendors.")
                    user.delete()  # Delete the user if vendor info is incomplete
                    return redirect('register')

                VendorProfile.objects.create(user=user, shop_name=shop_name, phone=form.cleaned_data.get("phone"))

            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')

    else:
        form = UserRegisterForm()

    return render(request, "products/register.html", {"form": form})


#  Single Login View for Users & Vendors
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)

            try:
                user_type = UserType.objects.get(user=user)
                
                if user_type.user_type == "vendor":
                    return redirect("vendor_dashboard")
                else:
                    return redirect("user_dashboard")  # Redirect users to view all products

            except UserType.DoesNotExist:
                messages.error(request, "User type not found. Please contact support.")
                return redirect("login")

        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "products/login.html")

# Admin Login (Fixed Credentials)
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session['is_admin'] = True  # Store Admin Session
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials")
            return redirect("admin_login")

    return render(request, "products/admin_login.html")

#  Admin Dashboard (Restrict Access)
@login_required
def admin_dashboard(request):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as admin first!")
        return redirect("admin_login")

    # Fetch all users and their associated shops (if any)
    users = User.objects.all()
    vendors = VendorProfile.objects.all()

    # Fetch products associated with each shop/vendor
    vendor_products = []
    for vendor in vendors:
        products = Product.objects.filter(vendor=vendor.user)  # Get products for this vendor
        vendor_products.append({
            'vendor': vendor,
            'products': products
        })

    return render(request, "products/admin_dashboard.html", {
        "users": users,
        "vendors": vendors,
        "vendor_products": vendor_products,  # Pass the vendor products as a list of dictionaries
    })
@login_required
def product_detail(request, product_id):
    # Get the product by ID
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'products/product_detail.html', {'product': product})
# Delete a User
@login_required
def delete_user(request, user_id):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as admin first!")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)

    # Check if user is a vendor and delete associated products if needed
    if hasattr(user, 'vendorprofile'):
        # Delete the vendor's products first
        VendorProfile.objects.filter(user=user).delete()

    user.delete()  # Delete the user

    messages.success(request, f"User {user.username} has been deleted.")
    return redirect('admin_dashboard')


# Delete a Vendor Shop (and associated products)
@login_required
def delete_vendor(request, vendor_id):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as admin first!")
        return redirect("admin_login")

    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    user = vendor.user  # Get the user associated with the vendor

    # Delete all products associated with this vendor
    products = Product.objects.filter(vendor=user)
    products.delete()

    # Now delete the vendor profile and the user associated with the shop
    vendor.delete()

    messages.success(request, f"Shop {vendor.shop_name} and its products have been deleted.")
    return redirect('admin_dashboard')


#  Logout for Admin, Users & Vendors
def logout_view(request):
    logout(request)
    return redirect("login")

# User Dashboard (Regular Users)
@login_required
def user_dashboard(request):
    query = request.GET.get('q', '')  # Get search query from URL parameters
    category_id = request.GET.get('category', None)  # Get selected category from URL parameters

    # Fetch all categories for the dropdown in the template
    categories = Category.objects.all()

    # Start by fetching all products
    products = Product.objects.all()

    if query:
        # Filter products based on the search query
        products = products.filter(name__icontains=query) | products.filter(description__icontains=query)

    if category_id:
        # Filter products based on the selected category
        products = products.filter(category_id=category_id)

    return render(request, "products/user_dashboard.html", {
        "products": products,
        "query": query,
        "categories": categories,
        "selected_category": category_id,  # Pass selected category to the template
    })


@login_required
def vendor_dashboard(request):
    # Ensure only vendors can access this dashboard
    if not hasattr(request.user, 'vendorprofile'):
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user  # Assign the logged-in vendor
            product.save()
            return redirect('vendor_dashboard')  # Redirect after adding product

    else:
        form = ProductForm()

    # Fetch only the products added by the logged-in vendor
    products = Product.objects.filter(vendor=request.user)

    return render(request, 'products/vendor_dashboard.html', {'form': form, 'products': products})
def vendor_products(request):
    # Fetch products that belong to the current logged-in vendor
    products = Product.objects.filter(vendor=request.user)
    
    context = {
        'products': products  # Pass the products to the template
    }
    return render(request, 'vendor_products.html', context)
@login_required
def edit_product(request, product_id):
    # Get the product that the logged-in vendor is trying to edit
    product = get_object_or_404(Product, id=product_id, vendor=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()  # Save the updated product details
            return redirect('vendor_dashboard')  # Redirect to vendor dashboard after saving

    else:
        form = ProductForm(instance=product)  # Pre-fill the form with the existing product data

    return render(request, 'products/edit_product.html', {'form': form})
@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=request.user)  # Ensure only the vendor can delete their product
    
    if request.method == 'POST':
        product.delete()  # Delete the product
        return redirect('vendor_dashboard')  # Redirect to vendor dashboard after deletion

    return render(request, 'products/delete_product.html', {'product': product})
@login_required
def search(request):
    query = request.GET.get('q', '')  # Get search query from URL parameters
    if query:
        # Search for products by name, description, or category
        products = Product.objects.filter(name__icontains=query) | Product.objects.filter(description__icontains=query)
    else:
        products = Product.objects.all()  # Show all products if no search query

    return render(request, 'products/search_results.html', {'products': products, 'query': query})