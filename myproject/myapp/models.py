from django.db import models

DIET = [('', 'choose diet'), ('gluten-free', 'gluten-free'), ('Keto', 'Keto'), ('Vegetarian', 'Vegetarian'), ('Vegan', 'Vegan')]


class Info(models.Model):
	rec_id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=100)
	diet = models.CharField(max_length=100, choices=DIET)
	created_on = models.DateField(auto_now_add=True)

