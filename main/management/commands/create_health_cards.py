from django.core.management.base import BaseCommand
from main.models import HealthCheckCard

class Command(BaseCommand):
    help = 'Creates default health check cards'

    def handle(self, *args, **options):
        default_cards = [
            {
                'title': 'Team Collaboration',
                'description': 'How well does the team collaborate and communicate?',
                'category': 'Team Dynamics'
            },
            {
                'title': 'Code Quality',
                'description': 'How satisfied are you with the quality of our codebase?',
                'category': 'Technical'
            },
            {
                'title': 'Documentation',
                'description': 'Is our documentation sufficient and up-to-date?',
                'category': 'Technical'
            },
            {
                'title': 'Working Environment',
                'description': 'Do you have the right tools and environment to do your job effectively?',
                'category': 'Work Environment'
            },
            {
                'title': 'Sprint Planning',
                'description': 'How effective is our sprint planning process?',
                'category': 'Process'
            },
            {
                'title': 'Technical Debt',
                'description': 'Are we managing technical debt appropriately?',
                'category': 'Technical'
            },
            {
                'title': 'Workload Balance',
                'description': 'Is the workload balanced appropriately across team members?',
                'category': 'Work Environment'
            },
            {
                'title': 'Team Morale',
                'description': 'How would you rate the overall team morale?',
                'category': 'Team Dynamics'
            },
            {
                'title': 'Knowledge Sharing',
                'description': 'How effectively is knowledge being shared within the team?',
                'category': 'Team Dynamics'
            },
            {
                'title': 'Testing Practices',
                'description': 'Are our testing practices sufficient for maintaining quality?',
                'category': 'Technical'
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for card_data in default_cards:
            # Check if the card already exists
            if not HealthCheckCard.objects.filter(title=card_data['title']).exists():
                # Create the card
                HealthCheckCard.objects.create(
                    title=card_data['title'],
                    description=card_data['description'],
                    category=card_data['category']
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created card: {card_data['title']}"))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f"Card already exists: {card_data['title']}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created_count} cards. {existing_count} cards already existed."
        )) 