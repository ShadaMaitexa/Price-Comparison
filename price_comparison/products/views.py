from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
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
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type = request.POST.get("user_type")
        shop_name = request.POST.get("shop_name")
        phone = request.POST.get("phone")

        # Validate input fields manually
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another one.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Create the user
        user = User.objects.create(username=username, email=email)
        user.set_password(password)
        user.save()

        # Create UserType entry
        user_type_entry = UserType.objects.create(user=user, user_type=user_type)

        # If user is a vendor, create VendorProfile
        if user_type == "vendor":
            if not shop_name:
                messages.error(request, "Shop Name is required for vendors.")
                user.delete()  # Rollback user creation
                return redirect("register")

            VendorProfile.objects.create(user=user, shop_name=shop_name, phone=phone)

        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")

    return render(request, "products/register.html")

#  Single Login View for Users & Vendors
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Fetch user type
            user_type = UserType.objects.filter(user=user).first()
            if user_type:
                if user_type.user_type == "vendor":
                    return redirect("vendor_dashboard")
                else:
                    return redirect("user_dashboard")  # Redirect users to view all products
            else:
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

        admin_username = "admin123"
        admin_password = "admin123"
        if username == admin_username and password == admin_password:
            request.session["is_admin"] = True  # Store admin session
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid admin credentials")
            return redirect("admin_login")

    return render(request, "products/admin_login.html")
#  Admin Dashboard (Restrict Access)
@login_required(login_url='/admin-login/')
def admin_dashboard(request):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as an admin first!")
        return redirect("admin_login")

    users = User.objects.all()
    vendors = VendorProfile.objects.all()

    vendor_products = []
    for vendor in vendors:
        products = Product.objects.filter(vendor=vendor.user)  # Fetch vendor's products
        vendor_products.append({
            'vendor': vendor,
            'products': products
        })

    return render(request, "products/admin_dashboard.html", {
        "users": users,
        "vendors": vendors,
        "vendor_products": vendor_products,
    })
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})

# Delete a User
@login_required
def delete_user(request, user_id):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as an admin first!")
        return redirect("admin_login")

    user = get_object_or_404(User, id=user_id)

    # Check if the user is a vendor
    if hasattr(user, 'vendorprofile'):
        # Delete vendor profile and associated products
        products = Product.objects.filter(vendor=user)
        products.delete()
        user.vendorprofile.delete()  # Delete vendor profile

    user.delete()  # Delete the user

    messages.success(request, f"User {user.username} has been deleted successfully.")
    return redirect('admin_dashboard')


# Delete a Vendor Shop (and associated products)
@login_required
def delete_vendor(request, vendor_id):
    if not request.session.get('is_admin'):
        messages.error(request, "You must log in as an admin first!")
        return redirect("admin_login")

    vendor = get_object_or_404(VendorProfile, id=vendor_id)
    user = vendor.user  # Get associated user

    # Delete all products related to this vendor
    Product.objects.filter(vendor=user).delete()

    # Delete the vendor profile and user account
    vendor.delete()
    user.delete()

    messages.success(request, f"Vendor {user.username} and their shop have been deleted.")
    return redirect('admin_dashboard')



#  Logout for Admin, Users & Vendors
def logout_view(request):
    logout(request)
    return redirect("login")
# products/views.py

@login_required
def user_dashboard(request):
    query = request.GET.get('q', '').strip()           # Get search query
    category_id = request.GET.get('category', '')        # Get category filter
    price_filter = request.GET.get('price', '')          # Get price order filter

    categories = Category.objects.all()                # Get all categories for dropdown
    products = Product.objects.all()                   # Start with all products

    # Apply search filter
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply price ordering filter
    if price_filter == 'low_to_high':
        products = products.order_by('price')
    elif price_filter == 'high_to_low':
        products = products.order_by('-price')

    # Fetch notifications (for simplicity, all unread notifications)
    from .models import Notification  # Or import at the top of the file
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')

    context = {
        "products": products,
        "query": query,
        "categories": categories,
        "selected_category": category_id,  # To preserve the selected category
        "selected_price": price_filter,    # To preserve the selected price filter
        "notifications": notifications,    # Pass notifications to the template
    }
    return render(request, "products/user_dashboard.html", context)

@login_required
def vendor_dashboard(request):
    # Ensure only vendors can access this dashboard
    if not hasattr(request.user, 'vendorprofile'):
        return redirect('user_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        image = request.FILES.get('image')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        # Manual validation (ensure required fields are filled)
        if not name or not price or not quantity or not image or not category_id:
            return render(request, 'products/vendor_dashboard.html', {
                'error_message': 'Please fill out all fields correctly.'
            })
        
        # Check if the price and quantity are valid numbers
        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            return render(request, 'products/vendor_dashboard.html', {
                'error_message': 'Price and quantity must be valid numbers.'
            })

        # Find the category
        category = Category.objects.get(id=category_id)

        # Create and save the product
        product = Product(
            name=name,
            price=price,
            quantity=quantity,
            image=image,
            description=description,
            category=category,
            vendor=request.user  # Assign the logged-in vendor
        )
        product.save()

        return redirect('vendor_dashboard')  # Redirect after adding product

    # Fetch only the products added by the logged-in vendor
    products = Product.objects.filter(vendor=request.user)

    # Fetch categories for the category dropdown
    categories = Category.objects.all()

    return render(request, 'products/vendor_dashboard.html', {
        'products': products,
        'categories': categories
    })
# products/views.py

@login_required
def edit_product(request, product_id):
    # Get the product that the logged-in vendor is trying to edit
    product = get_object_or_404(Product, id=product_id, vendor=request.user)

    if request.method == 'POST':
        # Get POST data for fields
        name = request.POST.get('name')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        # Validate input fields
        if not name or not price or not quantity or not category_id:
            return render(request, 'products/edit_product.html', {
                'error_message': 'Please fill out all fields correctly.',
                'product': product
            })

        # Check if the price and quantity are valid numbers
        try:
            new_price = float(price)
            quantity = int(quantity)
        except ValueError:
            return render(request, 'products/edit_product.html', {
                'error_message': 'Price and quantity must be valid numbers.',
                'product': product
            })

        # Find the category
        category = Category.objects.get(id=category_id)

        # Check if the price has changed before updating
        old_price = product.price

        # Update the product with the new data
        product.name = name
        product.price = new_price
        product.quantity = quantity
        product.description = description
        product.category = category

        # Only update the image if a new one was provided
        if image:
            product.image = image

        product.save()  # Save the updated product details

        # If the price has changed, create a notification
        if new_price != old_price:
            from .models import Notification  # Import here or at the top of the file
            Notification.objects.create(
                product=product,
                message=f"The price for '{product.name}' has changed from ${old_price} to ${new_price}."
            )

        return redirect('vendor_dashboard')  # Redirect to vendor dashboard after saving

    else:
        # Just display the existing product's details for the vendor to edit
        categories = Category.objects.all()  # Get available categories for the dropdown
        return render(request, 'products/edit_product.html', {
            'product': product,
            'categories': categories
        })

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=request.user)  # Ensure only the vendor can delete their product
    
    if request.method == 'POST':
        product.delete()  # Delete the product
        return redirect('vendor_dashboard')  # Redirect to vendor dashboard after deletion

    # If the request method is GET, show the confirmation page
    return render(request, 'products/delete_product.html', {'product': product})
@login_required
def search(request):
    query = request.GET.get('q', '').strip()

    if query:
        products = Product.objects.filter(name__icontains=query) | Product.objects.filter(description__icontains=query)
    else:
        products = Product.objects.all()

    return render(request, 'products/search_results.html', {'products': products, 'query': query})
