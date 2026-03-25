import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from datetime import timedelta

from todo.models import Category, Priority, Task, SubTask, Note

class Command(BaseCommand):
    help = 'Seeds the database with sample Categories, Priorities, Tasks, SubTasks, and Notes.'

    def handle(self, *args, **kwargs):
        fake = Faker()
        
        # 1. Get or create a User
        user = User.objects.first()
        if not user:
            user = User.objects.create_superuser('jonard', 'baterzalricho56@gmail.com', 'password123')
            self.stdout.write(self.style.SUCCESS('Created default superuser "jonard"'))

        # 2. Seed Priorities
        priorities = ['Low', 'Normal', 'High', 'Critical']
        priority_objs = []
        for p in priorities:
            obj, created = Priority.objects.get_or_create(name=p)
            priority_objs.append(obj)
            
        # 3. Seed Categories
        categories = ['Personal', 'Work', 'Urgent', 'Ideas', 'Shopping']
        category_objs = []
        for c in categories:
            obj, created = Category.objects.get_or_create(name=c)
            category_objs.append(obj)

        self.stdout.write(self.style.SUCCESS(f'Verified {len(priority_objs)} priorities and {len(category_objs)} categories.'))

        # 4. Seed Tasks
        statuses = ["Pending", "In Progress", "Completed"]
        
        tasks_created = 0
        subtasks_created = 0
        notes_created = 0
        
        self.stdout.write('Creating 15 random tasks with subtasks and notes...')
        
        for _ in range(15):
            # Pick a deadline
            days_offset = random.randint(-5, 15)
            deadline = timezone.now() + timedelta(days=days_offset)
            
            task = Task.objects.create(
                user=user,
                title=fake.catch_phrase(),
                description=fake.paragraph(nb_sentences=3),
                status=random.choice(statuses),
                category=random.choice(category_objs),
                priority=random.choice(priority_objs),
                deadline=deadline
            )
            tasks_created += 1
            
            # Seed SubTasks
            for __ in range(random.randint(0, 4)):
                SubTask.objects.create(
                    parent_task=task,
                    title=fake.sentence(nb_words=5),
                    status=random.choice(statuses)
                )
                subtasks_created += 1
                
            # Seed Notes
            for __ in range(random.randint(0, 3)):
                Note.objects.create(
                    task=task,
                    content=fake.paragraph(nb_sentences=2)
                )
                notes_created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {tasks_created} Tasks, {subtasks_created} SubTasks, and {notes_created} Notes!'))
