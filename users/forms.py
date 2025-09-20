from django import forms
from django.contrib.auth import get_user_model
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
