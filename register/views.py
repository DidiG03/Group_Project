from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from functools import wraps
from django.contrib.auth.views import LoginView

def redirect_if_authenticated(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Get user profile and redirect to appropriate dashboard
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.role == 'senior_manager':
                    return redirect('admin_dashboard')
                else:  # team_member
                    return redirect('dashboard')
            except UserProfile.DoesNotExist:
                return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Create your views here.
@redirect_if_authenticated
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after successful registration
            auth_login(response, user)
            messages.success(response, "Account created successfully!")
            
            # Redirect based on user role
            if user.profile.role == 'senior_manager':
                return redirect("admin_dashboard")
            else:  # team_member
                # For team members, check if approval is needed
                if user.profile.is_approved:
                    return redirect("dashboard")
                else:
                    messages.info(response, "Your account has been created and is awaiting approval.")
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
    """Page for team leaders and engineers to see while waiting for approval"""
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

@redirect_if_authenticated
def custom_login(request):
    return LoginView.as_view(template_name='registration/login.html')(request)
