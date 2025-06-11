from django import forms
from .models import ChitRegistration
from .models import AdminConfig
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    username=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter User Name'}))
    email=forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter Email Address'}))
    password1=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Enter Your Password'}))
    password2=forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'Enter Confirm Password'}))
    class Meta:
        model=User
        fields=['username','email','password1','password2']

class AdminConfigForm(forms.ModelForm):
    class Meta:
        model = AdminConfig
        fields = ['key', 'value']
       
class ChitForm(forms.ModelForm):

    class Meta:
        model = ChitRegistration
        fields = ['chit_Type', 'chit_Number', 'name', 'phoneNumber', 'address', 'village', 'district', 'num_Of_Chits','whatsapp']

    def __init__(self, *args, **kwargs):
        super(ChitForm, self).__init__(*args, **kwargs)
        self.fields['chit_Type'].widget.attrs['readonly'] = True
        self.fields['chit_Number'].widget.attrs['readonly'] = True
        self.fields['num_Of_Chits'].widget.attrs['readonly'] = True

    def clean_chit_Number(self):
        chit_number = self.cleaned_data.get('chit_Number')

        if not chit_number:
            raise forms.ValidationError("Chit Number cannot be empty.")

        if self.instance.pk:
            existing_chit = ChitRegistration.objects.get(pk=self.instance.pk)
            
            if existing_chit.chit_Number == chit_number:
                return chit_number

        if ChitRegistration.objects.filter(chit_Number=chit_number).exists():
            raise forms.ValidationError(f"Chit Number '{chit_number}' already exists. Please choose a different number.")

        return chit_number
