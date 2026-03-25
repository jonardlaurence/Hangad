from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from .forms import TaskForm, SubTaskForm, CategoryForm, PriorityForm, NoteForm
from .models import Category, Note, Priority, SubTask, Task


STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED = "Completed"
OPEN_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS)


def _social_provider_enabled(provider_id):
    provider_config = settings.SOCIALACCOUNT_PROVIDERS.get(provider_id, {})
    apps = provider_config.get("APPS")
    if apps:
        return True
    app = provider_config.get("APP")
    return bool(app)


class HangarinLoginView(LoginView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_login_enabled"] = _social_provider_enabled("google")
        context["github_login_enabled"] = _social_provider_enabled("github")
        return context


def _task_queryset(user):
    return (
        Task.objects.filter(user=user)
        .select_related("priority", "category")
        .prefetch_related("notes", "subtasks")
    )


def _decorate_tasks(task_list):
    now = timezone.now()

    for task in task_list:
        priority_name = (task.priority.name or "").lower()
        task.is_priority_alert = priority_name in {"high", "critical"}
        task.is_overdue = bool(
            task.deadline and task.status != STATUS_COMPLETED and task.deadline < now
        )
        task.preview_notes = list(task.notes.all())[:2]


@login_required
def task_list(request):
    tasks_base = _task_queryset(request.user).order_by("-created_at")
    filtered_tasks = tasks_base

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search_query:
        filtered_tasks = filtered_tasks.filter(title__icontains=search_query)
    if status_filter:
        filtered_tasks = filtered_tasks.filter(status=status_filter)

    paginator = Paginator(filtered_tasks, 6)
    page_number = request.GET.get("page")
    tasks = paginator.get_page(page_number)
    _decorate_tasks(tasks.object_list)

    context = {
        "tasks": tasks,
        "status_options": [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED],
        "summary": {
            "total": tasks_base.count(),
            "pending": tasks_base.filter(status=STATUS_PENDING).count(),
            "in_progress": tasks_base.filter(status=STATUS_IN_PROGRESS).count(),
            "completed": tasks_base.filter(status=STATUS_COMPLETED).count(),
        },
        "active_filters": {
            "q": search_query,
            "status": status_filter,
        },
    }
    return render(request, "tasks/task_list.html", context)


@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            messages.success(request, "Task created successfully.")
            return redirect("task_list")
    else:
        form = TaskForm()

    return render(request, "create_task.html", {"form": form})


@login_required
@require_POST
def complete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.status = STATUS_COMPLETED
    task.save(update_fields=["status", "updated_at"])
    messages.success(request, f'"{task.title}" marked as completed.')
    return redirect("task_list")


@login_required
@require_POST
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task_title = task.title
    task.delete()
    messages.success(request, f'"{task_title}" deleted.')
    return redirect("task_list")


@login_required
def dashboard(request):
    all_tasks = _task_queryset(request.user)
    today = timezone.localdate()
    total = all_tasks.count()
    completed = all_tasks.filter(status=STATUS_COMPLETED).count()
    pending = all_tasks.filter(status=STATUS_PENDING).count()
    in_progress = all_tasks.filter(status=STATUS_IN_PROGRESS).count()
    overdue = all_tasks.filter(
        status__in=OPEN_STATUSES,
        deadline__date__lt=today,
    ).count()
    due_today = all_tasks.filter(
        status__in=OPEN_STATUSES,
        deadline__date=today,
    ).count()
    completion_rate = round((completed / total) * 100) if total else 0

    urgent = list(
        all_tasks.filter(
            Q(priority__name__iexact="high") | Q(priority__name__iexact="critical"),
            status__in=OPEN_STATUSES,
        )
        .order_by("deadline", "-created_at")[:5]
    )
    upcoming = list(
        all_tasks.filter(status__in=OPEN_STATUSES, deadline__isnull=False)
        .order_by("deadline")[:5]
    )
    recent_tasks = list(all_tasks.order_by("-created_at")[:4])
    recent_notes = list(
        Note.objects.filter(task__user=request.user)
        .select_related("task")
        .order_by("-created_at")[:4]
    )
    category_breakdown = list(
        all_tasks.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total", "category__name")
    )

    max_category_total = max((item["total"] for item in category_breakdown), default=1)
    for item in category_breakdown:
        item["label"] = item["category__name"] or "Uncategorized"
        item["percentage"] = round((item["total"] / max_category_total) * 100)

    _decorate_tasks(urgent)
    _decorate_tasks(upcoming)
    _decorate_tasks(recent_tasks)

    context = {
        "total": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "overdue": overdue,
        "due_today": due_today,
        "completion_rate": completion_rate,
        "urgent": urgent,
        "upcoming": upcoming,
        "recent_tasks": recent_tasks,
        "recent_notes": recent_notes,
        "category_breakdown": category_breakdown,
    }
    return render(request, "dashboard.html", context)


@login_required
def subtask_list(request):
    subtasks = SubTask.objects.filter(parent_task__user=request.user).select_related('parent_task').order_by('-created_at')
    return render(request, "tasks/subtask_list.html", {"subtasks": subtasks, "title": "Sub Tasks", "subtitle": "Track smaller steps of your larger tasks."})

@login_required
def category_list(request):
    categories = Category.objects.annotate(tasks_linked=Count('tasks')).order_by('name')
    return render(request, "tasks/category_list.html", {"items": categories, "title": "Categories", "subtitle": "Your task categorization labels."})

@login_required
def priority_list(request):
    priorities = Priority.objects.annotate(tasks_linked=Count('tasks')).order_by('name')
    return render(request, "tasks/priority_list.html", {"items": priorities, "title": "Priorities", "subtitle": "Your task priority levels."})

@login_required
def note_list(request):
    notes = Note.objects.filter(task__user=request.user).select_related('task').order_by('-created_at')
    return render(request, "tasks/note_list.html", {"notes": notes, "title": "Notes", "subtitle": "Your collected task notes in one place."})

# CRUD CBVs

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Task'
        return context

class SubTaskCreateView(LoginRequiredMixin, CreateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('subtask_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Sub Task'
        return context

class SubTaskUpdateView(LoginRequiredMixin, UpdateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('subtask_list')

    def get_queryset(self):
        return super().get_queryset().filter(parent_task__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Sub Task'
        return context

class SubTaskDeleteView(LoginRequiredMixin, DeleteView):
    model = SubTask
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('subtask_list')

    def get_queryset(self):
        return super().get_queryset().filter(parent_task__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Sub Task'
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Category'
        return context

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Category'
        return context

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Category'
        return context

class PriorityCreateView(LoginRequiredMixin, CreateView):
    model = Priority
    form_class = PriorityForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('priority_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Priority'
        return context

class PriorityUpdateView(LoginRequiredMixin, UpdateView):
    model = Priority
    form_class = PriorityForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('priority_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Priority'
        return context

class PriorityDeleteView(LoginRequiredMixin, DeleteView):
    model = Priority
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('priority_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Priority'
        return context

class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('note_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Note'
        return context

class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'tasks/generic_form.html'
    success_url = reverse_lazy('note_list')

    def get_queryset(self):
        return super().get_queryset().filter(task__user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Note'
        return context

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'tasks/generic_confirm_delete.html'
    success_url = reverse_lazy('note_list')

    def get_queryset(self):
        return super().get_queryset().filter(task__user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_name'] = 'Note'
        return context
