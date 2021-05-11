from django.shortcuts import render
from .models import Info
from .forms import MyForm
from datetime import datetime



def home(request):
	all_info = Info.objects.all()
	return render(request, 'home.html', {'all_info': all_info})



def entry(request):
	form = MyForm()
	if request.method == 'POST':
		form = MyForm(request.POST)
		if form.is_valid():
			rec = Info(name=form.cleaned_data['name'], diet=form.cleaned_data['diet'])
			rec.save()
		else:
			return render(request,  'entry.html', {'form': form, 'error': 'Bad data entry.'})
		return render(request, 'entry.html', {'form': MyForm()})
	return render(request, 'entry.html', {'form': form})

