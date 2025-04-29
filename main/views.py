from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Project, Department, Team, ProjectComment, CommentReply, TeamJoinRequest, HealthCheckSession, HealthCheckCard, HealthCheckVote
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
from django.utils import timezone
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Create role-based decorators
def senior_manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'senior_manager':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "You don't have permission to access the senior manager dashboard.")
                return redirect('dashboard')
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found. Please contact an administrator.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')
    return _wrapped_view

def department_lead_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'department_lead':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "You don't have permission to access the department lead dashboard.")
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')
    return _wrapped_view

def team_leader_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            print(f"User: {request.user.username}, Profile role: {profile.role}")
            
            # Check if the user has a team leader role by either name
            if profile.role == 'team_leader':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "You don't have permission to access the team leader dashboard.")
                return redirect('dashboard')
        except Exception as e:
            print(f"Error in team_leader_required: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')
    return _wrapped_view

def engineer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'engineer':
                return view_func(request, *args, **kwargs)
            else:
                messages.warning(request, "You don't have permission to access the engineer dashboard.")
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('login')
    return _wrapped_view

def non_admin_required(view_func):
    """
    Decorator for views that checks that the logged-in user is not an admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            if not hasattr(request.user, 'profile') or request.user.profile.role not in ['senior_manager']:
                return view_func(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in non_admin_required: {str(e)}")
            return view_func(request, *args, **kwargs)
        messages.warning(request, "This page is not accessible for senior managers.")
        return redirect('admin_dashboard')
    return _wrapped_view

def admin_required(view_func):
    """
    Decorator for views that checks that the logged-in user is an admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            if hasattr(request.user, 'profile') and request.user.profile.role in ['senior_manager']:
                return view_func(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in admin_required: {str(e)}")
        messages.warning(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return _wrapped_view

# Create your views here.
def index(response, id):
    # Redirect to home or dashboard instead of using ToDoList
    return redirect('home')

@login_required
def home(response):
    # Check user role and redirect to appropriate dashboard
    try:
        profile = UserProfile.objects.get(user=response.user)
        if not profile.is_approved:
            return redirect('waiting_approval')
            
        # Redirect based on role
        if profile.role == 'senior_manager':
            return redirect('admin_dashboard')
        else:  # team_member
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(response, "User profile not found. Please contact an administrator.")
        return redirect('login')
    except Exception as e:
        messages.error(response, f"Error determining user role: {str(e)}")
        return redirect('login')

def create(response):
    # Redirect to dashboard instead of using CreateNewList and ToDoList
    return redirect('dashboard')

# Generic dashboard redirect view
@login_required
def dashboard(request):
    try:
        all_roles = UserProfile.objects.values_list('role', flat=True).distinct()
        print(f"All roles in the system: {list(all_roles)}")
        
        profile = UserProfile.objects.get(user=request.user)
        if not profile.is_approved:
            messages.warning(request, "Your account is still pending approval.")
            return redirect('waiting_approval')
        
        print(f"Current user: {request.user.username}, Role: {profile.role}")
        
        if profile.role == 'senior_manager':
            return redirect('admin_dashboard')
        else:
            user_teams = request.user.profile.teams.all()
            projects = Project.objects.filter(team__in=user_teams).order_by('-created_at')
            total_projects = projects.count()
            active_projects = projects.filter(status='active').count()
            completed_projects = projects.filter(status='completed').count()
            has_technical_role = bool(profile.technical_role)
            # Only allow add project if user is a team member (with is_team_leader) or department lead
            can_add_project = (profile.is_team_leader or profile.is_department_lead)
            context = {
                'user': request.user,
                'projects': projects,
                'user_teams': user_teams,
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'has_technical_role': has_technical_role,
                'can_add_project': can_add_project,
            }
            return render(request, "main/dashboard.html", context)
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact an administrator.")
        return redirect('login')
    except Exception as e:
        messages.error(request, f"Error determining user role: {str(e)}")
        return redirect('login')

# Engineer dashboard
@login_required
@engineer_required
def engineer_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'engineer':
            messages.warning(request, "You don't have permission to access the engineer dashboard.")
            if profile.role == 'senior_manager':
                return redirect('admin_dashboard')
            elif profile.role == 'department_lead':
                return redirect('department_lead_dashboard')
            elif profile.role == 'team_leader':
                return redirect('team_leader_dashboard')
            else:
                return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')
    
    # Get user's teams
    user_teams = request.user.profile.teams.all()
    
    # Get projects for user's teams
    projects = Project.objects.filter(team__in=user_teams).order_by('-created_at')
    
    context = {
        'user': request.user,
        'projects': projects,
        'teams': user_teams,
    }
    return render(request, "main/engineer_dashboard.html", context)

# Team Leader dashboard
@login_required
@team_leader_required
def team_leader_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'team_leader':
            messages.warning(request, "You don't have permission to access the team leader dashboard.")
            if profile.role == 'senior_manager':
                return redirect('admin_dashboard')
            elif profile.role == 'department_lead':
                return redirect('department_lead_dashboard')
            elif profile.role == 'engineer':
                return redirect('engineer_dashboard')
            else:
                return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')
    
    # Get user's teams
    user_teams = request.user.profile.teams.all()
    
    # Get projects for user's teams
    projects = Project.objects.filter(team__in=user_teams).order_by('-created_at')
    
    # Get team join requests for user's teams
    team_requests = TeamJoinRequest.objects.filter(team__in=user_teams, status='pending')
    
    context = {
        'user': request.user,
        'projects': projects,
        'teams': user_teams,
        'team_requests': team_requests,
    }
    return render(request, "main/team_leader_dashboard.html", context)

# Department Lead dashboard
@login_required
@department_lead_required
def department_lead_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'department_lead':
            messages.warning(request, "You don't have permission to access the department lead dashboard.")
            if profile.role == 'senior_manager':
                return redirect('admin_dashboard')
            elif profile.role == 'team_leader':
                return redirect('team_leader_dashboard')
            elif profile.role == 'engineer':
                return redirect('engineer_dashboard')
            else:
                return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')
    
    # Get user's department
    department = request.user.profile.department
    
    # Get teams in the department
    teams = Team.objects.filter(department=department)
    
    # Get projects for teams in the department
    projects = Project.objects.filter(team__in=teams).order_by('-created_at')
    
    context = {
        'user': request.user,
        'projects': projects,
        'teams': teams,
        'department': department,
    }
    return render(request, "main/department_lead_dashboard.html", context)

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
            
            # Get selected teams (returns a list of team ids)
            team_ids = request.POST.getlist('teams')
            
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
            
            # Update technical role and teams if profile exists
            try:
                profile = UserProfile.objects.get(user=user)
                if technical_role:
                    profile.technical_role = technical_role
                
                # Update teams (clear existing teams and add selected ones)
                profile.teams.clear()
                if team_ids:
                    teams = Team.objects.filter(id__in=team_ids)
                    profile.teams.add(*teams)
                
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
        
        # If senior manager, get company information
        company = None
        if profile.role == 'senior_manager':
            try:
                company = Company.objects.get(created_by=user)
            except Company.DoesNotExist:
                # If not found by created_by, check if user is in a company
                company = profile.company
            except:
                pass
        
    except Exception as e:
        profile = None
        company = None
    
    # Get all teams for the multi-select dropdown
    teams = Team.objects.all()
    
    # Get teams available for joining (exclude teams the user is already part of)
    user_teams = []
    if profile:
        user_teams = profile.teams.all()
    available_teams = Team.objects.exclude(id__in=[team.id for team in user_teams])
    
    # Get pending team join requests
    pending_requests = TeamJoinRequest.objects.filter(user=user, status='pending')
    
    # Render the settings template with context
    context = {
        'username': user.username,
        'user': user,
        'profile': profile,
        'company': company,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'teams': teams,  # Pass all teams to the template
        'available_teams': available_teams,  # Teams available for joining
        'pending_requests': pending_requests,  # Pending team join requests
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
    # Check if user has a technical role
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.technical_role:
            messages.warning(request, "You need to select a professional role in your settings before accessing project health features.")
            return redirect('settings')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('dashboard')

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
    # Check if user has a technical role
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.technical_role:
            messages.warning(request, "You need to select a professional role in your settings before updating project health.")
            return redirect('settings')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('dashboard')
        
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
    # Check if user has a technical role
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.technical_role:
            messages.warning(request, "You need to select a professional role in your settings before creating projects.")
            return redirect('settings')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('dashboard')
            
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
@senior_manager_required
def admin_dashboard(request):
    # Get all users
    user_profiles = UserProfile.objects.all().select_related('user', 'company')
    
    # Count all users and projects
    total_users = user_profiles.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='active').count()
    
    # Get pending employee approvals
    pending_approvals = UserProfile.objects.filter(is_approved=False)
    pending_count = pending_approvals.count()
    
    # Get pending project approvals
    pending_projects = Project.objects.filter(is_approved=False)
    pending_projects_count = pending_projects.count()
    
    # Get all projects
    projects = Project.objects.all()
    
    # Get all teams and departments
    teams = Team.objects.all().select_related('department').prefetch_related('team_members')
    departments = Department.objects.all()
    
    # Get pending team join requests
    pending_team_requests = TeamJoinRequest.objects.filter(status='pending').select_related('user', 'team')
    pending_team_requests_count = pending_team_requests.count()
    
    context = {
        'user': request.user,
        'user_profiles': user_profiles,
        'total_users': total_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'pending_approvals': pending_approvals,
        'pending_count': pending_count,
        'pending_projects': pending_projects,
        'pending_projects_count': pending_projects_count,
        'projects': projects,
        'teams': teams,
        'departments': departments,
        'pending_team_requests': pending_team_requests,
        'pending_team_requests_count': pending_team_requests_count,
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
@senior_manager_required
def approve_employee(request, user_id):
    if request.method == "POST":
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            
            # Verify the senior manager is from the same company
            if profile.company != request.user.profile.company:
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

# Add view to create a new team
@login_required
@admin_required
def create_team(request):
    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get('team_name')
            code = request.POST.get('team_code')
            department_id = request.POST.get('department')
            
            # Validate data
            if not name or not code or not department_id:
                messages.error(request, "All fields are required")
                return redirect('admin_dashboard')
            
            # Check if team code already exists
            if Team.objects.filter(code=code).exists():
                messages.error(request, f"Team code '{code}' already exists")
                return redirect('admin_dashboard')
                
            # Get department
            department = Department.objects.get(id=department_id)
            
            # Create the team
            team = Team.objects.create(
                name=name,
                code=code,
                department=department
            )
            
            messages.success(request, f"Team '{name}' has been created successfully!")
            
        except Exception as e:
            messages.error(request, f"Error creating team: {str(e)}")
            
    return redirect('admin_dashboard')

# Add view for requesting to join a team
@login_required
def request_team_join(request):
    if request.method == "POST":
        try:
            team_id = request.POST.get('team_id')
            
            # Validate data
            if not team_id:
                messages.error(request, "Team selection is required")
                return redirect('settings')
            
            # Check if user has a technical role
            profile = UserProfile.objects.get(user=request.user)
            if not profile.technical_role:
                messages.error(request, "You must select a professional role before requesting to join a team")
                return redirect('settings')
            
            # Get the team
            team = Team.objects.get(id=team_id)
            
            # Check if user is already in the team
            if team in profile.teams.all():
                messages.info(request, f"You are already a member of '{team.name}'")
                return redirect('settings')
                
            # Check if a request is already pending
            if TeamJoinRequest.objects.filter(user=request.user, team=team, status='pending').exists():
                messages.info(request, f"You already have a pending request to join '{team.name}'")
                return redirect('settings')
                
            # Create the request
            TeamJoinRequest.objects.create(
                user=request.user,
                team=team
            )
            
            messages.success(request, f"Your request to join '{team.name}' has been submitted and is pending approval.")
            
        except Team.DoesNotExist:
            messages.error(request, "Team not found")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found")
        except Exception as e:
            messages.error(request, f"Error submitting request: {str(e)}")
            
    return redirect('settings')

# Add view for approving a team join request
@login_required
def approve_team_request(request, request_id):
    if request.method == "POST":
        try:
            # Get the join request
            join_request = TeamJoinRequest.objects.get(id=request_id, status='pending')
            
            # Debug logging
            print(f"Request ID: {request_id}, User: {request.user.username}, Role: {request.user.profile.role}")
            
            # Check if user is an admin or team leader of the team
            profile = UserProfile.objects.get(user=request.user)
            
            # Debug info
            print(f"Profile role: {profile.role}")
            is_admin = profile.role in ['senior_manager', 'admin'] 
            is_team_leader = profile.role == 'team_leader' and join_request.team in profile.teams.all()
            
            print(f"Is admin: {is_admin}, Is team leader: {is_team_leader}")
            print(f"User teams: {list(profile.teams.all().values_list('name', flat=True))}")
            print(f"Request team: {join_request.team.name}")
            
            if not (is_admin or is_team_leader):
                messages.error(request, "You don't have permission to approve this request")
                return redirect('dashboard')
            
            # Update the request status
            join_request.status = 'approved'
            join_request.approved_at = timezone.now()
            join_request.approved_by = request.user
            join_request.save()
            
            # Add user to the team
            user_profile = UserProfile.objects.get(user=join_request.user)
            user_profile.teams.add(join_request.team)
            
            messages.success(request, f"{join_request.user.first_name} {join_request.user.last_name} has been added to '{join_request.team.name}'.")
            
        except TeamJoinRequest.DoesNotExist:
            messages.error(request, "Join request not found or already processed")
        except Exception as e:
            messages.error(request, f"Error approving request: {str(e)}")
    
    # Redirect based on user role
    if hasattr(request.user, 'profile') and request.user.profile.role == 'team_leader':
        return redirect('team_leader_dashboard')
    else:
        return redirect('admin_dashboard')

# Add view for rejecting a team join request
@login_required
def reject_team_request(request, request_id):
    if request.method == "POST":
        try:
            # Get the join request
            join_request = TeamJoinRequest.objects.get(id=request_id, status='pending')
            
            # Debug logging
            print(f"Request ID: {request_id}, User: {request.user.username}, Role: {request.user.profile.role}")
            
            # Check if user is an admin or team leader of the team
            profile = UserProfile.objects.get(user=request.user)
            
            # Debug info
            print(f"Profile role: {profile.role}")
            is_admin = profile.role in ['senior_manager', 'admin']
            is_team_leader = profile.role == 'team_leader' and join_request.team in profile.teams.all()
            
            print(f"Is admin: {is_admin}, Is team leader: {is_team_leader}")
            print(f"User teams: {list(profile.teams.all().values_list('name', flat=True))}")
            print(f"Request team: {join_request.team.name}")
            
            if not (is_admin or is_team_leader):
                messages.error(request, "You don't have permission to reject this request")
                return redirect('dashboard')
            
            # Update the request status
            join_request.status = 'rejected'
            join_request.save()
            
            messages.success(request, f"Request from {join_request.user.first_name} {join_request.user.last_name} to join '{join_request.team.name}' has been rejected.")
            
        except TeamJoinRequest.DoesNotExist:
            messages.error(request, "Join request not found or already processed")
        except Exception as e:
            messages.error(request, f"Error rejecting request: {str(e)}")
    
    # Redirect based on user role
    if hasattr(request.user, 'profile') and request.user.profile.role == 'team_leader':
        return redirect('team_leader_dashboard')
    else:
        return redirect('admin_dashboard')

# Add view to create a new department
@login_required
@admin_required
def create_department(request):
    if request.method == "POST":
        try:
            # Get form data
            name = request.POST.get('department_name')
            code = request.POST.get('department_code')
            
            # Validate data
            if not name or not code:
                messages.error(request, "All fields are required")
                return redirect('admin_dashboard')
            
            # Check if department code already exists
            if Department.objects.filter(code=code).exists():
                messages.error(request, f"Department code '{code}' already exists")
                return redirect('admin_dashboard')
                
            # Create the department
            department = Department.objects.create(
                name=name,
                code=code
            )
            
            messages.success(request, f"Department '{name}' has been created successfully!")
            
        except Exception as e:
            messages.error(request, f"Error creating department: {str(e)}")
            
    return redirect('admin_dashboard')

# Team Health Check views
@login_required
def team_selection(request):
    """View for users to select a team for health checks"""
    # Get user's teams
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        if user_role == 'senior_manager':
            user_teams = Team.objects.all()
        else:
            user_teams = request.user.profile.teams.all()
    else:
        messages.warning(request, "You need to join a team before you can participate in health checks.")
        return redirect('settings')
    
    # Get recent health check sessions for each team
    team_sessions = {}
    for team in user_teams:
        sessions = HealthCheckSession.objects.filter(team=team).order_by('-created_at')[:5]
        team_sessions[team.id] = sessions
    
    context = {
        'user': request.user,
        'user_teams': user_teams,
        'team_sessions': team_sessions,
        'role': user_role,
    }
    
    return render(request, "main/team_selection.html", context)

@login_required
def create_health_session(request):
    """View for creating a new health check session"""
    if request.method == "POST":
        team_id = request.POST.get('team_id')
        session_name = request.POST.get('session_name')
        card_ids = request.POST.getlist('card_ids')
        
        # Validate data
        if not team_id or not session_name or not card_ids:
            messages.error(request, "All fields are required")
            return redirect('team_selection')
        
        try:
            # Get team
            team = Team.objects.get(id=team_id)
            
            # Check if user belongs to the team
            if team not in request.user.profile.teams.all() and request.user.profile.role != 'senior_manager':
                messages.error(request, "You can only create sessions for teams you belong to")
                return redirect('team_selection')
            
            # Create the session
            session = HealthCheckSession.objects.create(
                team=team,
                created_by=request.user,
                name=session_name
            )
            
            # Add cards to the session
            cards = HealthCheckCard.objects.filter(id__in=card_ids, is_active=True)
            session.cards.add(*cards)
            
            messages.success(request, f"Health check session '{session_name}' created successfully!")
            return redirect('view_health_session', session_id=session.id)
            
        except Team.DoesNotExist:
            messages.error(request, "Team not found")
        except Exception as e:
            messages.error(request, f"Error creating session: {str(e)}")
    
    # For GET requests, show the form
    user_teams = request.user.profile.teams.all()
    active_cards = HealthCheckCard.objects.filter(is_active=True)
    
    context = {
        'user': request.user,
        'user_teams': user_teams,
        'cards': active_cards,
    }
    
    return render(request, "main/create_health_session.html", context)

@login_required
def view_health_session(request, session_id):
    """View to display a health check session and collect votes"""
    try:
        session = HealthCheckSession.objects.get(id=session_id)
        
        # Check if user belongs to the team
        if session.team not in request.user.profile.teams.all() and request.user.profile.role != 'senior_manager':
            messages.error(request, "You can only view sessions for teams you belong to")
            return redirect('team_selection')
        
        # Get user's votes for this session
        user_votes = HealthCheckVote.objects.filter(session=session, user=request.user)
        voted_card_ids = [vote.card.id for vote in user_votes]
        
        # Prepare context
        context = {
            'user': request.user,
            'session': session,
            'cards': session.cards.all(),
            'voted_card_ids': voted_card_ids,
            'user_votes': {vote.card.id: vote for vote in user_votes},
            'team_members': session.team.team_members.all(),
        }
        
        return render(request, "main/view_health_session.html", context)
        
    except HealthCheckSession.DoesNotExist:
        messages.error(request, "Session not found")
        return redirect('team_selection')
    except Exception as e:
        messages.error(request, f"Error viewing session: {str(e)}")
        return redirect('team_selection')

@login_required
def submit_vote(request):
    """API view to submit a vote for a card"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    try:
        session_id = request.POST.get('session_id')
        card_id = request.POST.get('card_id')
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        
        # Validate data
        if not session_id or not card_id or not score:
            return JsonResponse({"error": "Missing required fields"}, status=400)
        
        # Get session and card
        session = HealthCheckSession.objects.get(id=session_id)
        card = HealthCheckCard.objects.get(id=card_id)
        
        # Check if user belongs to the team
        if session.team not in request.user.profile.teams.all() and request.user.profile.role != 'senior_manager':
            return JsonResponse({"error": "You can only vote in sessions for teams you belong to"}, status=403)
        
        # Create or update vote
        vote, created = HealthCheckVote.objects.update_or_create(
            session=session,
            card=card,
            user=request.user,
            defaults={
                'score': score,
                'comment': comment
            }
        )
        
        # Return success
        return JsonResponse({
            "success": True, 
            "message": "Vote submitted successfully",
            "created": created
        })
        
    except HealthCheckSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)
    except HealthCheckCard.DoesNotExist:
        return JsonResponse({"error": "Card not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def team_health_summary(request, team_id):
    """View to display a summary of health check results for a team"""
    try:
        team = Team.objects.get(id=team_id)
        
        # Check if user belongs to the team
        if team not in request.user.profile.teams.all() and request.user.profile.role != 'senior_manager':
            messages.error(request, "You can only view summaries for teams you belong to")
            return redirect('team_selection')
        
        # Get all sessions for this team
        sessions = HealthCheckSession.objects.filter(team=team).order_by('-created_at')
        
        # Calculate avg scores per session
        session_scores = {}
        for session in sessions:
            session_scores[session.id] = session.get_average_score()
        
        # Calculate overall team health score (average of all sessions)
        overall_score = sum(session_scores.values()) / len(session_scores) if session_scores else 0
        
        # Get trending data (last 5 sessions)
        trend_data = []
        for session in sessions[:5]:
            trend_data.append({
                'date': session.created_at.strftime('%Y-%m-%d'),
                'score': session_scores[session.id]
            })
        
        context = {
            'user': request.user,
            'team': team,
            'sessions': sessions,
            'session_scores': session_scores,
            'overall_score': overall_score,
            'trend_data': list(reversed(trend_data)),  # Reverse to show oldest to newest
        }
        
        return render(request, "main/team_health_summary.html", context)
        
    except Team.DoesNotExist:
        messages.error(request, "Team not found")
        return redirect('team_selection')
    except Exception as e:
        messages.error(request, f"Error viewing summary: {str(e)}")
        return redirect('team_selection')

@login_required
@admin_required
def manage_health_cards(request):
    """Admin view to manage health check cards"""
    # Get all cards
    cards = HealthCheckCard.objects.all().order_by('category', 'title')
    
    # Handle form submission for creating/editing cards
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'create':
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            
            if title and description and category:
                HealthCheckCard.objects.create(
                    title=title,
                    description=description,
                    category=category
                )
                messages.success(request, f"Card '{title}' created successfully")
            else:
                messages.error(request, "All fields are required")
                
        elif action == 'update':
            card_id = request.POST.get('card_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            category = request.POST.get('category')
            
            if card_id and title and description and category:
                card = HealthCheckCard.objects.get(id=card_id)
                card.title = title
                card.description = description
                card.category = category
                card.save()
                messages.success(request, f"Card '{title}' updated successfully")
            else:
                messages.error(request, "All fields are required")
                
        elif action == 'toggle_status':
            card_id = request.POST.get('card_id')
            if card_id:
                card = HealthCheckCard.objects.get(id=card_id)
                card.is_active = not card.is_active
                card.save()
                status = "activated" if card.is_active else "deactivated"
                messages.success(request, f"Card '{card.title}' {status} successfully")
            else:
                messages.error(request, "Card ID is required")
                
        # Refresh cards after changes
        cards = HealthCheckCard.objects.all().order_by('category', 'title')
    
    context = {
        'user': request.user,
        'cards': cards,
        'categories': set([card.category for card in cards]),
    }
    
    return render(request, "main/manage_health_cards.html", context)

# Add view for joining a team using code and password
@login_required
def join_team_password(request):
    if request.method == "POST":
        try:
            # Get form data
            team_code = request.POST.get('team_code')
            team_password = request.POST.get('team_password')
            
            # Validate data
            if not team_code or not team_password:
                messages.error(request, "Team code and password are required")
                return redirect('settings')
            
            # Check if user has a technical role
            profile = UserProfile.objects.get(user=request.user)
            if not profile.technical_role:
                messages.error(request, "You must select a professional role before joining a team")
                return redirect('settings')
            
            # Get the team by code
            try:
                team = Team.objects.get(code=team_code)
            except Team.DoesNotExist:
                messages.error(request, f"No team found with code '{team_code}'")
                return redirect('settings')
            
            # Check if user is already in the team
            if team in profile.teams.all():
                messages.info(request, f"You are already a member of '{team.name}'")
                return redirect('settings')
                
            # Check if a request is already pending
            if TeamJoinRequest.objects.filter(user=request.user, team=team, status='pending').exists():
                messages.info(request, f"You already have a pending request to join '{team.name}'")
                return redirect('settings')
            
            # Verify team password
            if not team.password:
                messages.error(request, f"Team '{team.name}' does not allow direct password joining. Please request to join instead.")
                return redirect('settings')
                
            if team.password != team_password:
                messages.error(request, "Incorrect team password")
                return redirect('settings')
            
            # Add user to the team directly (no approval needed since password is correct)
            profile.teams.add(team)
            
            # Log the successful join
            logger.info(f"User {request.user.username} joined team {team.name} using password")
            
            messages.success(request, f"You have successfully joined '{team.name}'!")
            
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found")
        except Exception as e:
            messages.error(request, f"Error joining team: {str(e)}")
            
    return redirect('settings')

# Add view for updating a team password
@login_required
def update_team_password(request, team_id):
    if request.method == "POST":
        try:
            # Get the team
            team = Team.objects.get(id=team_id)
            
            # Check if the user has permission (user is a team leader in this team)
            profile = UserProfile.objects.get(user=request.user)
            
            # Only team leaders in this team can update the password
            if profile.role != 'team_leader' or team not in profile.teams.all():
                messages.error(request, "You don't have permission to update this team's password")
                return redirect('team_leader_dashboard')
            
            # Check if remove password was requested
            if request.POST.get('remove_password'):
                team.password = None
                team.save()
                messages.success(request, f"Password removed for team '{team.name}'")
                return redirect('team_leader_dashboard')
            
            # Get the new password
            password = request.POST.get('password')
            
            # Update or set the password
            team.password = password
            team.save()
            
            messages.success(request, f"Password updated for team '{team.name}'")
            
        except Team.DoesNotExist:
            messages.error(request, "Team not found")
        except UserProfile.DoesNotExist:
            messages.error(request, "User profile not found")
        except Exception as e:
            messages.error(request, f"Error updating team password: {str(e)}")
            
    return redirect('team_leader_dashboard')

@login_required
@senior_manager_required
def assign_department_lead(request, department_id):
    if request.method == "POST":
        user_id = request.POST.get("department_lead")
        try:
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)
            department = Department.objects.get(id=department_id)
            # Set department lead boolean and assign department
            profile.is_department_lead = True
            profile.department = department
            profile.save()
            messages.success(request, f"{user.get_full_name()} assigned as Department Lead.")
        except Exception as e:
            messages.error(request, f"Error assigning department lead: {str(e)}")
    return redirect("admin_dashboard")

@login_required
@senior_manager_required
def add_team_members(request, team_id):
    if request.method == "POST":
        user_ids = request.POST.getlist("team_members")
        team_leader_id = request.POST.get("team_leader")
        try:
            team = Team.objects.get(id=team_id)
            # Assign team leader
            if team_leader_id:
                leader_user = User.objects.get(id=team_leader_id)
                leader_profile = UserProfile.objects.get(user=leader_user)
                leader_profile.is_team_leader = True
                leader_profile.teams.add(team)
                leader_profile.save()
            # Add members
            for user_id in user_ids:
                user = User.objects.get(id=user_id)
                profile = UserProfile.objects.get(user=user)
                profile.teams.add(team)
                profile.save()
            messages.success(request, "Team leader and members updated.")
        except Exception as e:
            messages.error(request, f"Error updating team: {str(e)}")
    return redirect("admin_dashboard")

# Team Member dashboard
@login_required
def team_member_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'team_member':
            messages.warning(request, "You don't have permission to access the team member dashboard.")
            if profile.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('login')
    
    # Get user's teams
    user_teams = request.user.profile.teams.all()
    
    # Get projects for user's teams
    projects = Project.objects.filter(team__in=user_teams).order_by('-created_at')
    
    context = {
        'user': request.user,
        'projects': projects,
        'teams': user_teams,
    }
    return render(request, "main/team_member_dashboard.html", context)


