from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Address

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'date_of_birth', 'avatar'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

class AddressForm(forms.ModelForm):
    """Form for adding and editing addresses"""
    
    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'company', 'address_line_1',
            'address_line_2', 'city', 'county', 'postcode', 'country',
            'phone', 'is_default'
        ]
        widgets = {
            'address_line_2': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'company': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'county': forms.TextInput(attrs={'placeholder': 'Optional'}),
        }


class UserRegisterForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)
    is_newsletter_subscribed = forms.BooleanField(required=False, label='Subscribe to newsletter')
    marketing_emails = forms.BooleanField(required=False, label='Receive marketing emails')
    sms_notifications = forms.BooleanField(required=False, label='Receive SMS notifications')
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'is_newsletter_subscribed', 'marketing_emails', 'sms_notifications',
            'password1', 'password2'
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
        user.phone = self.cleaned_data['phone']
        user.is_newsletter_subscribed = self.cleaned_data['is_newsletter_subscribed']
        user.marketing_emails = self.cleaned_data['marketing_emails']
        user.sms_notifications = self.cleaned_data['sms_notifications']
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Form for user login"""
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False, label='Remember me')
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise ValidationError('Invalid email or password.')
            elif not user.is_active:
                raise ValidationError('This account is inactive.')
        
        return cleaned_data
