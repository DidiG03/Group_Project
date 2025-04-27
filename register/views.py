from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login

# Create your views here.
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after successful registration
            auth_login(response, user)
            messages.success(response, "Account created successfully!")
            
            # Redirect based on user role
            if user.profile.role == 'admin':
                return redirect("admin_dashboard")
            else:
                # For employees, show a message that their account needs approval
                messages.info(response, "Your account has been created and is awaiting admin approval.")
                return redirect("waiting_approval")
        else:
            # If there are form errors, render the custom template with form data
            context = {
                'form': form,
                'errors': form.errors,
                'username': response.POST.get('username', ''),
                'full_name': response.POST.get('full_name', ''),
                'email': response.POST.get('email', ''),
                'dob': response.POST.get('dob', ''),
                'company_name': response.POST.get('company_name', ''),
                'company_code': response.POST.get('company_code', ''),
                'role': response.POST.get('role', ''),
            }
            return render(response, "register/register.html", context)
    else:
        form = RegisterForm()
        # For a GET request, just render the empty form
        return render(response, "register/register.html", {"form": form})

@login_required
def waiting_approval(request):
    """Page for employees to see while waiting for approval"""
    # Get the user profile
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.is_approved:
            # If already approved, redirect to dashboard
            return redirect('dashboard')
        
        # If not approved, show the waiting page
        return render(request, "register/waiting_approval.html", {
            'user': request.user,
            'profile': profile
        })
        
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')
