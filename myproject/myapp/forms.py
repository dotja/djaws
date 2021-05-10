from django import forms
from .models import Info, DIET


class MyForm(forms.Form):
	name = forms.CharField(
		required=True,
		widget=forms.TextInput(
			attrs={'placeholder': 'Name', 'maxlength': '100'}
		),
	)
	diet = forms.CharField(
		required=True,
		widget=forms.Select(choices=DIET, attrs={'placeholder': 'diet'}),
	)