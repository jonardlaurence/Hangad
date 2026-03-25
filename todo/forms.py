from django import forms

from .models import Category, Note, Priority, SubTask, Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "deadline", "status", "category", "priority"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Enter a concise task title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Add the details, context, or next steps for this task",
                    "rows": 5,
                }
            ),
            "deadline": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["deadline"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["category"].queryset = Category.objects.order_by("name")
        self.fields["priority"].queryset = Priority.objects.order_by("name")

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select form-select-lg"
            elif isinstance(field.widget, forms.Textarea):
                css_class = "form-control form-control-lg task-textarea"
            else:
                css_class = "form-control form-control-lg"

            field.widget.attrs["class"] = css_class

            if name == "deadline":
                field.widget.attrs["min"] = "2000-01-01T00:00"


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["task", "content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "placeholder": "Enter your note here...",
                    "rows": 3,
                    "class": "form-control form-control-lg",
                }
            ),
            "task": forms.Select(attrs={"class": "form-select form-select-lg"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['task'].queryset = Task.objects.filter(user=user)


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ["parent_task", "title", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Sub task title"}),
            "status": forms.Select(attrs={"class": "form-select form-select-lg"}),
            "parent_task": forms.Select(attrs={"class": "form-select form-select-lg"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['parent_task'].queryset = Task.objects.filter(user=user)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Category Name"}),
        }


class PriorityForm(forms.ModelForm):
    class Meta:
        model = Priority
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control form-control-lg", "placeholder": "Priority Name"}),
        }
