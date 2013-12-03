from django.db import models
from django.contrib.auth.models import User

class MUser(models.Model):
  user = models.ForeignKey(User)
  name = models.CharField(max_length=200, default=user, blank=True)
  following = models.TextField(blank=True)
  info = models.CharField(max_length=1500, default="There is currently no other information available", blank=True)
  picture = models.ImageField(upload_to='profile_pictures', default='default/stickman.jpg', blank = True)
  def __unicode__(self):
    return self.name

class Recipe(models.Model):
  name = models.CharField(max_length=200)
  orig_author = models.CharField(max_length=500, default="", blank=True)
  curr_author = models.ForeignKey('MUser')
  is_closed = models.BooleanField()
  food_type = models.CharField(max_length=200, blank=True)
  drink_flag = models.BooleanField()
  time_edited = models.DateTimeField(auto_now=True)
  instructions = models.TextField(blank=True)
  serves_num = models.IntegerField(null = True)
  picture = models.ImageField(upload_to="recipe-photos", default='default/emptyplate.jpg', blank=True)
  def __unicode__(self):
    return self.name

class Matrix(models.Model):
  col = models.IntegerField(null = True)
  row = models.IntegerField(null = True)
  value = models.FloatField(null = True)
  metrics = models.CharField(max_length = 10, blank = True)
  def __unicode__(self):
    return str(self.row) + ", " + str(self.col) + ": " + str(self.value)

class FoodWord(models.Model):
  name = models.CharField(max_length = 200)
  def __unicode__(self):
    return self.id + ": " + self.name 

class Comment(models.Model):
  author = models.ForeignKey('MUser')
  recipe = models.ForeignKey('Recipe')
  text = models.CharField(max_length=200)
  time_edited = models.DateTimeField(auto_now=True)
  def __unicode__(self):
    return self.author.name + "," + self.recipe.name + ": " + self.text

class Suggestion(models.Model):
  author = models.ForeignKey('MUser')
  recipe = models.ForeignKey('Recipe')
  text = models.CharField(max_length=200)
  time_edited = models.DateTimeField(auto_now=True)
  def __unicode__(self):
    return self.author.name + "," + self.recipe.name + ": " + self.text

class Rating(models.Model):
  author = models.ForeignKey('MUser')
  recipe = models.ForeignKey('Recipe')
  rating_value = models.FloatField(null = True)
  time_edited = models.DateTimeField(auto_now=True)
  def __unicode__(self):
    return self.author.name + "," + self.recipe.name + ": " + str(self.rating_value)

