from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name='home'), name="root"),  # Redirect root to home
    path("<int:id>", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("create/", views.create, name="create"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("chat/", views.chat, name="chat"),
    path("settings/", views.settings, name="settings"),
    path("project-health/", views.project_health, name="project_health"),
    path("save-project-health/", views.save_project_health, name="save_project_health"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-projects/", views.admin_projects, name="admin_projects"),
    path("add-project/", views.add_project, name="add_project"),
    path("get-project-comments/<int:project_id>/", views.get_project_comments, name="get_project_comments"),
    path("approve-employee/<int:user_id>/", views.approve_employee, name="approve_employee"),
    path("reject-employee/<int:user_id>/", views.reject_employee, name="reject_employee"),
    path("approve-project/<int:project_id>/", views.approve_project, name="approve_project"),
    path("reject-project/<int:project_id>/", views.reject_project, name="reject_project"),
    path("delete-user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("add-comment-reply/", views.add_comment_reply, name="add_comment_reply"),
    path("logout/", views.logout_view, name="logout"),  # Custom logout view
    
    # Role-specific dashboards
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # New team-related URLs
    path("create-team/", views.create_team, name="create_team"),
    path("create-department/", views.create_department, name="create_department"),
    path("request-team-join/", views.request_team_join, name="request_team_join"),
    path("approve-team-request/<int:request_id>/", views.approve_team_request, name="approve_team_request"),
    path("reject-team-request/<int:request_id>/", views.reject_team_request, name="reject_team_request"),
    
    # Team Health Check URLs
    path("team-selection/", views.team_selection, name="team_selection"),
    path("create-health-session/", views.create_health_session, name="create_health_session"),
    path("view-health-session/<int:session_id>/", views.view_health_session, name="view_health_session"),
    path("submit-vote/", views.submit_vote, name="submit_vote"),
    path("team-health-summary/<int:team_id>/", views.team_health_summary, name="team_health_summary"),
    path("manage-health-cards/", views.manage_health_cards, name="manage_health_cards"),
    path("join-team-password/", views.join_team_password, name="join_team_password"),
    path("update-team-password/<int:team_id>/", views.update_team_password, name="update_team_password"),
    path("assign-department-lead/<int:department_id>/", views.assign_department_lead, name="assign_department_lead"),
    path("add-team-members/<int:team_id>/", views.add_team_members, name="add_team_members"),
    path("team-health-session-summary/<int:session_id>/", views.team_health_session_summary, name="team_health_session_summary"),
]