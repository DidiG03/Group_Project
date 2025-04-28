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
    password = models.CharField(max_length=100, blank=True, null=True, help_text="Password for joining this team directly")
    
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

class HealthCheckCard(models.Model):
    """Cards that team members vote on during health check sessions"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class HealthCheckSession(models.Model):
    """A health check session for a team"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="health_sessions")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_sessions")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=200)
    cards = models.ManyToManyField(HealthCheckCard, related_name="sessions")
    
    def __str__(self):
        return f"{self.team.name} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_average_score(self):
        """Calculate the average score across all cards in this session"""
        votes = HealthCheckVote.objects.filter(session=self)
        if not votes.exists():
            return 0
        return votes.aggregate(models.Avg('score'))['score__avg']

class HealthCheckVote(models.Model):
    """A vote on a card by a team member"""
    SCORE_CHOICES = [
        (1, 'Strongly Disagree'),
        (2, 'Disagree'),
        (3, 'Neutral'),
        (4, 'Agree'),
        (5, 'Strongly Agree'),
    ]
    
    session = models.ForeignKey(HealthCheckSession, on_delete=models.CASCADE, related_name="votes")
    card = models.ForeignKey(HealthCheckCard, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="health_votes")
    score = models.IntegerField(choices=SCORE_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('session', 'card', 'user')
        
    def __str__(self):
        return f"{self.user.username}'s vote on {self.card.title}"
