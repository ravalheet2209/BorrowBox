from allauth.socialaccount.forms import SignupForm
from django import forms

class MyCustomSocialSignupForm(SignupForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        required=True,
        label="Password (for future manual login)"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        required=True,
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw1 and pw2 and pw1 != pw2:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned_data

    def save(self, request):
        user = super().save(request)
        
        # Set the custom password
        password = self.cleaned_data.get("password")
        user.set_password(password)
        user.save()
        
        return user
