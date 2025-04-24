from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import ToDoList, Item, Project, Department, Team, ProjectComment, CommentReply
from .forms import CreateNewList
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from functools import wraps
from django.core.exceptions import PermissionDenied
from register.models import UserProfile, Company
import os
from django.contrib.auth import logout as auth_logout

# Create role-based decorators
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "You don't have permission to access the admin dashboard.")
                return redirect('dashboard')  # Redirect to employee dashboard
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')
    return _wrapped_view

def non_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role != 'admin':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "Admins should use the admin dashboard.")
                return redirect('admin_dashboard')  # Redirect to admin dashboard
        except Exception as e:
            # If profile doesn't exist or other error, still allow access
            return view_func(request, *args, **kwargs)
    return _wrapped_view

# Create your views here.
def index(response, id):
    ls = ToDoList.objects.get(id=id)
    if response.method == "POST":
        print(response.POST)
        if response.POST.get("save"):
            for item in ls.item_set.all():
                if response.POST.get("c" + str(item.id)) == "clicked":
                    item.complete = True
                else:
                    item.complete = False
                item.save()

        elif response.POST.get("newItem"):
            txt = response.POST.get("new")

            if len(txt) > 2:
                ls.item_set.create(text=txt, complete=False)
            else:
                print("invalid")


    return render(response, "main/list.html", {"ls": ls})

@login_required
def home(response):
    # Check user role and redirect to appropriate dashboard
    try:
        profile = UserProfile.objects.get(user=response.user)
        if profile.role == 'admin':
            return redirect('admin_dashboard')
        else:
            # Check if employee is approved
            if not profile.is_approved:
                return redirect('waiting_approval')
            return redirect('dashboard')
    except Exception as e:
        messages.error(response, f"Error determining user role: {str(e)}")
        return redirect('login')

def create(response):
    if response.method == "POST":
        form = CreateNewList(response.POST)

        if form.is_valid():
            n = form.cleaned_data["name"]
            t = ToDoList(name=n)
            t.save()
        return HttpResponseRedirect("/%i" %t.id)
    else:
        form = CreateNewList()
    return render(response, "main/create.html", {"form": form})

# Add dashboard view - protected route
@login_required
@non_admin_required
def dashboard(request):
    print("Dashboard view is being called!")
    
    # Check if the user is approved
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.is_approved and profile.role == 'employee':
            messages.warning(request, "Your account is still pending approval from an administrator.")
            return redirect('waiting_approval')
    except UserProfile.DoesNotExist:
        pass
    
    # Get projects data - only show approved projects
    projects = Project.objects.filter(is_approved=True).order_by('-created_at')
    
    # Get user's pending projects
    pending_projects = Project.objects.filter(
        created_by=request.user,
        is_approved=False
    ).order_by('-created_at')
    
    # Get stats - only count approved projects
    total_projects = Project.objects.filter(is_approved=True).count()
    active_projects = Project.objects.filter(status='active', is_approved=True).count()
    completed_projects = Project.objects.filter(status='completed', is_approved=True).count()
    team_members = User.objects.count()
    
    # Get teams and departments for dropdown
    teams = Team.objects.all()
    departments = Department.objects.all()
    
    # Check if we need to create default data
    if teams.count() == 0:
        # Create a default department
        default_dept = Department.objects.create(name="General", code="GEN")
        # Create a default team
        Team.objects.create(name="Default Team", code="DEF", department=default_dept)
        # Refresh data
        teams = Team.objects.all()
        departments = Department.objects.all()
    
    # Get current user's username to display in the dashboard
    context = {
        'username': request.user.username,
        'user': request.user,
        'projects': projects,
        'pending_projects': pending_projects,
        'teams': teams,
        'departments': departments,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'team_members': team_members
    }
    return render(request, "main/dashboard.html", context)

# Add chat view - protected route
@login_required
def chat(request):
    context = {
        'username': request.user.username,
        'user': request.user
    }
    return render(request, "main/chat.html", context)

# Add settings view - protected route
@login_required
def settings(request):
    user = request.user
    
    # Handle form submission
    if request.method == "POST":
        try:
            # Get form data
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            new_password = request.POST.get('new_password', '')
            technical_role = request.POST.get('role', '')
            
            # Update user profile
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            
            # Update password if provided and valid
            if new_password:
                user.set_password(new_password)
                # This will require the user to login again
                messages.info(request, "Password updated. Please login again.")
            
            user.save()
            
            # Update technical role if profile exists
            try:
                profile = UserProfile.objects.get(user=user)
                if technical_role:
                    profile.technical_role = technical_role
                    profile.save()
            except UserProfile.DoesNotExist:
                pass
            
            # If the password was not changed, display success message
            if not new_password:
                messages.success(request, "Profile information updated successfully!")
            return redirect('settings')
            
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    # Try to get user profile information
    try:
        profile = UserProfile.objects.get(user=user)
        
        # If admin, get company information
        company = None
        if profile.role == 'admin':
            try:
                company = Company.objects.get(created_by=user)
            except Company.DoesNotExist:
                pass
            
    except Exception as e:
        profile = None
        company = None
    
    # Render the settings template with context
    context = {
        'username': user.username,
        'user': user,
        'profile': profile,
        'company': company,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    
    return render(request, "main/settings.html", context)

# Add a save_settings view for handling form submission
@login_required
def save_settings(request):
    if request.method == "POST":
        try:
            user = request.user
            
            # Get form data
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            new_password = request.POST.get('new_password', '')
            
            # Update user profile
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            
            # Update password if provided
            if new_password:
                user.set_password(new_password)
                user.save()
                # This will log the user out
                messages.info(request, "Password updated. Please login again.")
                return redirect('login')
            
            user.save()
            messages.success(request, "Profile information updated successfully!")
            
        except Exception as e:
            messages.error(request, f"Error updating profile: {str(e)}")
    
    return redirect('settings')

# Add project health view - protected route
@login_required
@non_admin_required
def project_health(request):
    # Get all projects for the dropdown
    projects = Project.objects.all().order_by('name')
    
    # Get project comments with prefetched replies
    comments = ProjectComment.objects.select_related('project', 'user').prefetch_related('replies__user').order_by('-created_at')
    
    # Add health data directly to each project object for easier access in the template
    for project in projects:
        # Convert health status to percentage for the slider
        health_percentage = 50  # Default middle value
        if project.health == 'poor':
            health_percentage = 20
        elif project.health == 'needs_work':
            health_percentage = 50
        elif project.health == 'good':
            health_percentage = 85
            
        # Add attributes directly to the project object for template access
        project.health_percentage = health_percentage
    
    context = {
        'username': request.user.username,
        'user': request.user,
        'projects': projects,
        'comments': comments
    }
    return render(request, "main/project_health.html", context)

# Add save project health view - protected route
@login_required
@non_admin_required
def save_project_health(request):
    """Handle form submission to save project health updates"""
    if request.method == "POST":
        try:
            # Get form data
            project_id = request.POST.get('project_id')
            health_percentage = request.POST.get('health_percentage')
            comment = request.POST.get('comment', '')
            
            # Validate data
            if not project_id or not health_percentage:
                messages.error(request, "Missing required fields")
                return redirect('project_health')
            
            # Convert percentage to health status
            health_percentage = int(health_percentage)
            if health_percentage < 30:
                health_status = 'poor'
            elif health_percentage < 70:
                health_status = 'needs_work'
            else:
                health_status = 'good'
                
            # Get the project
            project = Project.objects.get(id=project_id)
            
            # Check if the project is being marked as completed early
            mark_completed = request.POST.get('mark_completed')
            if mark_completed:
                completion_date = request.POST.get('completion_date')
                completion_notes = request.POST.get('completion_notes', '')
                
                if completion_date:
                    # Update project status to completed early
                    project.status = 'completed_early'
                    project.completed_early_date = completion_date
                    project.completion_notes = completion_notes
                    
                    # Handle file upload if provided
                    if 'documentation' in request.FILES:
                        file = request.FILES['documentation']
                        # Check file size (max 10MB)
                        if file.size > 10 * 1024 * 1024:
                            messages.error(request, "File size exceeds the maximum allowed (10MB)")
                            return redirect('project_health')
                            
                        # Check file extension
                        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                        file_ext = os.path.splitext(file.name)[1].lower()
                        if file_ext not in allowed_extensions:
                            messages.error(request, "File type not supported. Please upload PDF or image files only.")
                            return redirect('project_health')
                            
                        # Save the file
                        project.documentation = file
                    
                    # Add a comment about early completion
                    ProjectComment.objects.create(
                        project=project,
                        user=request.user,
                        text=f"Project marked as completed early on {completion_date}. {completion_notes}"
                    )
                    
                    messages.success(request, f"Project '{project.name}' has been marked as completed early.")
                else:
                    messages.error(request, "Completion date is required when marking a project as completed early.")
                    return redirect('project_health')
            else:
                # Update project health only
                project.health = health_status
                
                # Add a comment if provided
                if comment:
                    ProjectComment.objects.create(
                        project=project,
                        user=request.user,
                        text=f"Health Update ({health_percentage}%): {comment}"
                    )
                    
                messages.success(request, f"Project health updated successfully for '{project.name}'")
            
            # Save changes
            project.save()
            
        except Project.DoesNotExist:
            messages.error(request, "Project not found. Please select a valid project.")
        except Exception as e:
            messages.error(request, f"Error updating project health: {str(e)}")
    
    return redirect('project_health')

# Add project view - protected route
@login_required
@non_admin_required
def add_project(request):
    """Handle form submission to add a new project"""
    # Get teams and departments for the form dropdown
    teams = Team.objects.all()
    departments = Department.objects.all()
    
    # Check if we need to create default data if none exists
    if teams.count() == 0:
        # Create a default department
        default_dept = Department.objects.create(name="General", code="GEN")
        # Create a default team
        Team.objects.create(name="Default Team", code="DEF", department=default_dept)
        # Refresh data
        teams = Team.objects.all()
        departments = Department.objects.all()
    
    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            team_id = request.POST.get('team')
            department_id = request.POST.get('department')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date', '')
            status = request.POST.get('status', 'active')
            health = request.POST.get('health', 'good')
            
            # Check if name already exists
            if Project.objects.filter(name=name).exists():
                messages.error(request, f"A project with the name '{name}' already exists.")
                return redirect('add_project')
                
            # Get the team and department
            team = Team.objects.get(id=team_id)
            department = Department.objects.get(id=department_id)
            
            # Create new project - admins' projects are auto-approved
            project = Project.objects.create(
                name=name,
                description=description,
                created_by=request.user,
                team=team,
                department=department,
                start_date=start_date,
                end_date=end_date if end_date else None,
                status=status,
                health=health,
                is_approved=False  # All projects require approval by default
            )
            
            # Add current user as a member
            project.members.add(request.user)
            
            messages.success(request, f"Project '{name}' created successfully and is pending admin approval.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
            # Render the form again with existing data
            context = {
                'username': request.user.username,
                'user': request.user,
                'teams': teams,
                'departments': departments
            }
            return render(request, "main/add_project.html", context)
    
    # For GET requests, render the form
    context = {
        'username': request.user.username,
        'user': request.user,
        'teams': teams,
        'departments': departments
    }
    return render(request, "main/add_project.html", context)

# Add admin dashboard view - protected route
@login_required
@admin_required
def admin_dashboard(request):
    # Get all users
    users = User.objects.all()
    
    # Get user profiles
    user_profiles = UserProfile.objects.select_related('user', 'company').all()
    
    # Get pending employee approvals for companies where this admin is the creator
    admin_companies = Company.objects.filter(created_by=request.user)
    pending_approvals = UserProfile.objects.filter(
        company__in=admin_companies,
        is_approved=False
    ).exclude(user=request.user).select_related('user', 'company').order_by('company__name')
    
    # Count of pending approvals
    pending_count = pending_approvals.count()
    
    # Get projects data
    projects = Project.objects.select_related('created_by', 'team', 'department').all()
    
    # Get pending project approvals
    company_employees = UserProfile.objects.filter(company__in=admin_companies).values_list('user_id', flat=True)
    pending_projects = Project.objects.filter(
        created_by_id__in=company_employees,
        is_approved=False
    ).select_related('created_by', 'team', 'department').order_by('-created_at')
    
    # Count of pending project approvals
    pending_projects_count = pending_projects.count()
    
    # Get stats
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='active').count()
    
    context = {
        'username': request.user.username,
        'user': request.user,
        'users': users,
        'user_profiles': user_profiles,
        'projects': projects,
        'total_users': total_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'pending_approvals': pending_approvals,
        'pending_count': pending_count,
        'pending_projects': pending_projects,
        'pending_projects_count': pending_projects_count,
    }
    return render(request, "main/admin_dashboard.html", context)

# Add admin projects view - protected route
@login_required
@admin_required
def admin_projects(request):
    # Get all projects with related data
    projects = Project.objects.select_related('created_by', 'team', 'department').all().order_by('-created_at')
    
    # Get user profiles for team assignments
    user_profiles = UserProfile.objects.exclude(role='admin').select_related('user').all()
    
    # Get existing comments
    comments = ProjectComment.objects.select_related('project', 'user').all().order_by('-created_at')
    
    # Handle comment form submission
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'add_comment':
            project_id = request.POST.get('project_id')
            comment_text = request.POST.get('comment_text')
            
            if project_id and comment_text:
                try:
                    project = Project.objects.get(id=project_id)
                    
                    # Create new comment
                    ProjectComment.objects.create(
                        project=project,
                        user=request.user,
                        text=comment_text
                    )
                    
                    messages.success(request, "Comment added successfully!")
                except Project.DoesNotExist:
                    messages.error(request, "Project not found.")
                except Exception as e:
                    messages.error(request, f"Error adding comment: {str(e)}")
        
        # Redirect to avoid form resubmission
        return redirect('admin_projects')
    
    context = {
        'username': request.user.username,
        'user': request.user,
        'projects': projects,
        'user_profiles': user_profiles,
        'comments': comments,
    }
    return render(request, "main/admin_projects.html", context)

# API endpoint to get project comments
@login_required
def get_project_comments(request, project_id):
    try:
        # Get the project
        project = Project.objects.get(id=project_id)
        
        # Check if user has access to this project
        if request.user.profile.role != 'admin' and request.user not in project.members.all():
            return JsonResponse({"error": "You don't have permission to view these comments"}, status=403)
        
        # Get comments for the project with prefetched replies
        comments = ProjectComment.objects.filter(project=project).prefetch_related('replies__user').order_by('-created_at')
        
        # Format comments for JSON response
        comment_list = []
        for comment in comments:
            # Get replies for this comment
            replies = []
            for reply in comment.replies.all():
                replies.append({
                    'id': reply.id,
                    'author': reply.user.username,
                    'text': reply.text,
                    'date': reply.created_at.strftime('%b %d, %Y %H:%M')
                })
                
            comment_list.append({
                'id': comment.id,
                'author': comment.user.username,
                'text': comment.text,
                'date': comment.created_at.strftime('%b %d, %Y %H:%M'),
                'replies': replies
            })
        
        return JsonResponse({"comments": comment_list})
    
    except Project.DoesNotExist:
        return JsonResponse({"error": "Project not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Add mark_comment_read view to handle AJAX requests
@login_required
def mark_comment_read(request, comment_id):
    if request.method == "POST":
        try:
            comment = ProjectComment.objects.get(id=comment_id)
            
            # Check if user is part of the project
            if request.user in comment.project.members.all():
                # Add user to read_by relationship
                comment.read_by.add(request.user)
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "User not part of this project"}, status=403)
        except ProjectComment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Comment not found"}, status=404)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

# Add view to approve an employee
@login_required
@admin_required
def approve_employee(request, user_id):
    if request.method == "POST":
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            
            # Verify the admin is from the same company
            admin_companies = Company.objects.filter(created_by=request.user)
            if profile.company not in admin_companies:
                messages.error(request, "You can only approve employees from your own company.")
                return redirect('admin_dashboard')
            
            # Update approval status
            profile.is_approved = True
            profile.save()
            
            messages.success(request, f"User {profile.user.username} has been approved.")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
        except Exception as e:
            messages.error(request, f"Error approving user: {str(e)}")
            
    return redirect('admin_dashboard')

# Add view to reject an employee
@login_required
@admin_required
def reject_employee(request, user_id):
    if request.method == "POST":
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            
            # Verify the admin is from the same company
            admin_companies = Company.objects.filter(created_by=request.user)
            if profile.company not in admin_companies:
                messages.error(request, "You can only reject employees from your own company.")
                return redirect('admin_dashboard')
            
            # Get the user to delete
            user = profile.user
            
            # Delete the user (this will cascade to the profile)
            user.delete()
            
            messages.success(request, f"User {user.username} has been rejected and removed.")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
        except Exception as e:
            messages.error(request, f"Error rejecting user: {str(e)}")
            
    return redirect('admin_dashboard')

# Add view to approve a project
@login_required
@admin_required
def approve_project(request, project_id):
    if request.method == "POST":
        try:
            project = Project.objects.get(id=project_id)
            
            # Check if the admin is part of the same company
            admin_companies = Company.objects.filter(created_by=request.user)
            creator_profile = UserProfile.objects.get(user=project.created_by)
            
            if creator_profile.company not in admin_companies:
                messages.error(request, "You can only approve projects from your own company.")
                return redirect('admin_dashboard')
                
            # Update approval status
            project.is_approved = True
            project.save()
            
            # Create a project comment to notify the team
            ProjectComment.objects.create(
                project=project,
                user=request.user,
                text=f"Project has been approved by {request.user.username}."
            )
            
            messages.success(request, f"Project '{project.name}' has been approved.")
        except Project.DoesNotExist:
            messages.error(request, "Project not found.")
        except Exception as e:
            messages.error(request, f"Error approving project: {str(e)}")
    
    return redirect('admin_dashboard')

# Add view to reject a project
@login_required
@admin_required
def reject_project(request, project_id):
    if request.method == "POST":
        try:
            project = Project.objects.get(id=project_id)
            
            # Check if the admin is part of the same company
            admin_companies = Company.objects.filter(created_by=request.user)
            creator_profile = UserProfile.objects.get(user=project.created_by)
            
            if creator_profile.company not in admin_companies:
                messages.error(request, "You can only reject projects from your own company.")
                return redirect('admin_dashboard')
            
            # Store project name for the success message
            project_name = project.name
            project_creator = project.created_by
            
            # Delete the project
            project.delete()
            
            # Notify via messaging system (if implemented)
            # For now, we'll just show a message to the admin
            messages.success(request, f"Project '{project_name}' has been rejected and removed.")
            
            # In a real app, you might want to send an email notification to the creator
            
        except Project.DoesNotExist:
            messages.error(request, "Project not found.")
        except Exception as e:
            messages.error(request, f"Error rejecting project: {str(e)}")
    
    return redirect('admin_dashboard')

# Add view to delete a user
@login_required
@admin_required
def delete_user(request, user_id):
    if request.method == "POST":
        try:
            # Get the user to delete
            user_to_delete = User.objects.get(id=user_id)
            profile_to_delete = UserProfile.objects.get(user=user_to_delete)
            
            # Verify the admin is from the same company
            admin_companies = Company.objects.filter(created_by=request.user)
            if profile_to_delete.company not in admin_companies:
                messages.error(request, "You can only remove users from your own company.")
                return redirect('admin_dashboard')
            
            # Store user info for the success message
            username = user_to_delete.username
            
            # Delete the user (this will cascade to the profile)
            user_to_delete.delete()
            
            messages.success(request, f"User {username} has been removed from the team.")
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found.")
        except Exception as e:
            messages.error(request, f"Error removing user: {str(e)}")
            
    return redirect('admin_dashboard')

# Add view to handle comment replies
@login_required
def add_comment_reply(request):
    if request.method == "POST":
        try:
            # Get the comment ID from the form
            comment_id = request.POST.get('comment_id')
            reply_text = request.POST.get('reply_text')
            
            # Validate inputs
            if not comment_id or not reply_text:
                messages.error(request, "Comment ID and reply text are required.")
                return redirect('project_health')
            
            # Get the comment
            comment = ProjectComment.objects.get(id=comment_id)
            
            # Create the reply
            reply = CommentReply.objects.create(
                comment=comment,
                user=request.user,
                text=reply_text
            )
            
            messages.success(request, "Your reply has been added successfully.")
            
        except ProjectComment.DoesNotExist:
            messages.error(request, "Comment not found.")
        except Exception as e:
            messages.error(request, f"Error adding reply: {str(e)}")
    
    # Redirect back to project health page
    return redirect('project_health')

# Add a custom logout view
def logout_view(request):
    auth_logout(request)
    return redirect('login')


