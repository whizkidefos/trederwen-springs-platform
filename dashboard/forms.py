from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()

class AdminUserForm(UserCreationForm):
    """Form for creating admin users"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    admin_title = forms.CharField(max_length=100, required=False)
    admin_department = forms.CharField(max_length=100, required=False)
    admin_bio = forms.CharField(widget=forms.Textarea, required=False)
    is_superuser = forms.BooleanField(required=False, label='Superuser status')
    is_staff = forms.BooleanField(required=False, label='Staff status (can access Django admin)')
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 
            'admin_title', 'admin_department', 'admin_bio',
            'is_superuser', 'is_staff', 'password1', 'password2'
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('This email is already in use.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Use email as username
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.admin_title = self.cleaned_data['admin_title']
        user.admin_department = self.cleaned_data['admin_department']
        user.admin_bio = self.cleaned_data['admin_bio']
        user.is_superuser = self.cleaned_data['is_superuser']
        user.is_staff = self.cleaned_data['is_staff']
        user.user_type = 'admin'  # Set user type to admin
        
        if commit:
            user.save()
        return user

class AdminUserEditForm(forms.ModelForm):
    """Form for editing admin users"""
    admin_title = forms.CharField(max_length=100, required=False)
    admin_department = forms.CharField(max_length=100, required=False)
    admin_bio = forms.CharField(widget=forms.Textarea, required=False)
    is_superuser = forms.BooleanField(required=False, label='Superuser status')
    is_staff = forms.BooleanField(required=False, label='Staff status (can access Django admin)')
    is_active = forms.BooleanField(required=False, label='Active')
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 
            'admin_title', 'admin_department', 'admin_bio',
            'is_superuser', 'is_staff', 'is_active'
        ]
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already in use.')
        return email
