from django import forms
from django.contrib.auth.models import User
from core.models import (
    StudentProfile, Classroom, Subject, Assignment,
    Submission, SubmissionAttachment, StudentAssignment
)
from core.utils.otp_service import normalize_phone


class StudentRegisterProfileForm(forms.ModelForm):
    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.filter(is_active=True),
        required=True,
        empty_label="— Sinfingizni tanlang —",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none'
        })
    )

    class Meta:
        model = StudentProfile
        fields = ['first_name', 'last_name', 'classroom', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Ismingiz',
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Familiyangiz',
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 dark:file:bg-blue-900/30 dark:file:text-blue-300 hover:file:bg-blue-100'
            })
        }


class AssignmentForm(forms.ModelForm):
    classrooms = forms.ModelMultipleChoiceField(
        queryset=Classroom.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500'}),
        label="Biriktiriladigan sinflar"
    )

    class Meta:
        model = Assignment
        fields = [
            'title', 'subject', 'classrooms', 'description', 'content',
            'attachment', 'video_url', 'assigned_date', 'start_time', 'due_date', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Vazifa mavzusi...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Qisqacha tavsif...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Vazifa to\'liq matni, topshiriqlar, shartlar...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'attachment': forms.FileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 file:text-blue-700'}),
            'video_url': forms.URLInput(attrs={
                'placeholder': 'https://youtube.com/watch?v=...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'assigned_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submission_text']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Javobingiz, yechim matni yoki izohingizni shu yerga yozing...',
                'class': 'w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            })
        }


class TeacherReviewForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['review_status', 'teacher_feedback']
        widgets = {
            'review_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'teacher_feedback': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'O\'quvchiga izoh, baho yoki kamchiliklar...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            })
        }


class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['first_name', 'last_name', 'classroom', 'phone_number', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'classroom': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+998901234567', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        return normalize_phone(phone)


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'grade_level', 'academic_year', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Masalan: 1-A', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'grade_level': forms.NumberInput(attrs={'min': 1, 'max': 11, 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'academic_year': forms.TextInput(attrs={'placeholder': '2025-2026', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Matematika', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'code': forms.TextInput(attrs={'placeholder': 'MATH-01', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'icon': forms.TextInput(attrs={'placeholder': 'book, calculator, globe...', 'class': 'w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'}),
        }
