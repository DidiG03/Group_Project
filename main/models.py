from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="teams")
    
    def __str__(self):
        return self.name

class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
        ('completed_early', 'Completed Early'),
    ]
    
    HEALTH_CHOICES = [
        ('good', 'Good Health'),
        ('needs_work', 'Needs Work'),
        ('poor', 'Poor Health'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    health = models.CharField(max_length=20, choices=HEALTH_CHOICES, default='good')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="projects")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="projects")
    members = models.ManyToManyField(User, related_name="projects")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False, help_text="Whether this project is approved by admin")
    completed_early_date = models.DateField(null=True, blank=True, help_text="Date when project was marked as completed early")
    completion_notes = models.TextField(blank=True, null=True, help_text="Notes about project completion")
    documentation = models.FileField(upload_to='project_files/', blank=True, null=True, help_text="Project documentation or files")
    
    def __str__(self):
        return self.name

class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name="read_comments", blank=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.project.name}"

class CommentReply(models.Model):
    comment = models.ForeignKey(ProjectComment, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Comment Replies"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply by {self.user.username} to comment {self.comment.id}"

class TeamJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_requests")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="join_requests")
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_team_requests")
    
    class Meta:
        unique_together = ('user', 'team')
        
    def __str__(self):
        return f"{self.user.username}'s request to join {self.team.name} ({self.get_status_display()})"
