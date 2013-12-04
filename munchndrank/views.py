from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.http import HttpResponse, Http404

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
# Used to generate a one-time-use token to verify a user's email address
from django.contrib.auth.tokens import default_token_generator
# Used to send mail from within Django
from django.core.mail import send_mail
from mimetypes import guess_type
from django.middleware.csrf import get_token
from copy import deepcopy
import sys, traceback, json 

from munchndrank.models import *
from munchndrank.rank import *
from munchndrank.forms import *

# Action for the default munchndrank route

@login_required
def home(request):
  # home view after log in
  return render(request, 'yum/home.html', {})

def top_recipe(request):
  # top_recipe (don't need to log in)
  return render(request, 'yum/top_recipe.html', {})

# update rating for a given recipe and user_id
@login_required
def update_rating(request):
  context = {}
  errors = []
  context['errors'] = errors;
  recipe_id = -1;
  value = -1.0;
  if not request.method == 'POST':
    errors.append('Not Post')
  if not 'recipe_id' in request.POST or not request.POST['recipe_id']:
    errors.append('No recipe id')
  else:
    recipe_id = int(request.POST['recipe_id'])
  if not 'value' in request.POST or not request.POST['value']:
    errors.append('No value')
  else:
    value = float(request.POST['value'])
  
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');

  muser = MUser.objects.get(id=request.user.id)
  recipe = Recipe.objects.get(id=recipe_id)
  check = Rating.objects.filter(author=muser).filter(recipe=recipe).exists()
  if not check:
    new_rating = Rating(author=muser,
                        recipe=recipe,
                        rating_value=value)
    new_rating.save()
    context['time_edited'] = str(new_rating.time_edited)
  else:
    old_rating = Rating.objects.filter(author=muser, recipe=recipe)[0]
    old_rating.rating_value = value
    old_rating.save()
    context['time_edited'] = str(old_rating.time_edited)

  context['success'] = 1
  json_data = json.dumps(context);
  return HttpResponse(json_data, content_type='application/json');

# Helper function for getting set of followed users
# @user_id current user id
# returns the set of users which current user follows
def get_following_set(user_id):
  following = MUser.objects.get(id=user_id).following.split(';')
  following_set = set()
  for f in following:
    if not f == '':
      following_set.add(int(f))
  return following_set

# Helper function to find the average rating for a recipe
# returns 2-tuple (a,b)
# @recipe = Recipe object
# @muser = current MUser object 
# a = avg_rating, -1.0 if not found
# b = user_rating, -1.0 if not found
def get_recipe_rating(recipe, muser):
  check = Rating.objects.filter(recipe=recipe).exists()
  if check:
    ratings = Rating.objects.filter(recipe=recipe)
    total = ratings.aggregate(Sum('rating_value'))
    avg_rating = total['rating_value__sum'] / ratings.count()
    if ratings.filter(author=muser).exists():
      user_rating = ratings.get(author=muser).rating_value
      return (avg_rating, user_rating)
    else:
      return (avg_rating , -1.0)
  else:
    return (-1.0, -1.0)

@login_required
def add_stream_page(request):
  # get a list of suggested streams and print to website
  # for now, we return the entire user list
  context = {}
  user_id = int(MUser.objects.get(name=request.user).id)
  all_users = MUser.objects.all().exclude(id=user_id)
  users = []
  following_set = get_following_set(request.user.id)
  for u in all_users:
    user = {}
    user['name'] = u.name
    user['id'] = u.id
    user['followed'] = 0
    if u.id in following_set:
      user['followed'] = 1
    users.append(user)
  context['users'] = users;
  return render(request, 'yum/addstream.html', context)

@login_required
def follow_stream(request):
  # takes ajax request and either follows/unfollows the stream 
  context = {};
  errors = [];
  context['errors'] = errors;
  if not request.method == 'POST':
    errors.append('Not post method');
  user_id = -1;
  is_followed = 0;
  if not 'user_id' in request.POST or not request.POST['user_id']:
    errors.append('No user_id')
  else:
    user_id = int(request.POST['user_id'])
  if not 'is_followed' in request.POST or not request.POST['is_followed']:
    errors.append('No is_followed')
  else:
    is_followed = int(request.POST['is_followed'])
 
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');

  muser = MUser.objects.get(id=request.user.id)
  following_set = get_following_set(request.user.id)
  if not is_followed:
    following_set.add(user_id)
  else:
    if user_id in following_set:
      following_set.remove(user_id)
  following_list = list(following_set);
  following_string = ''
  for f in following_list:
    following_string = following_string + str(f) + ";"
  muser.following = following_string
  muser.save()
  context['user_id'] = user_id;
  context['is_followed'] = not is_followed
  context['success'] = 1
  json_data = json.dumps(context);
  return HttpResponse(json_data, content_type='application/json'); 

@login_required
def search_stream(request):
  context = {};
  errors = [];
  context['errors'] = errors;
  search_term = '';
  if not request.method == 'POST':
    errors.append('Not post method');
  if not 'search_term' in request.POST or not request.POST['search_term']:
    errors.append('Error in search text');
  else:
    search_term = request.POST['search_term'];
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');
  
  following_set = get_following_set(request.user.id)
  found_users = MUser.objects.filter(name__contains=search_term).exclude(id=request.user.id)
  users = []
  for u in found_users:
    user = {}
    user['name'] = u.name
    user['id'] = u.id
    user['followed'] = 0
    if u.id in following_set:
      user['followed'] = 1
    users.append(user)
  context['users'] = users;
  s_response = render_to_string('yum/searchstream_template.html', context)
  json_data = json.dumps({'success': 1, 'text': s_response})
  return HttpResponse(json_data, content_type='application/json')

@login_required
def foodstream(request):
  errors_f = []
  food = []
  muser = MUser.objects.get(id=request.user.id)
  try:
    following_list = list(get_following_set(request.user.id))
    followed_users = MUser.objects.filter(id__in=following_list)
    r_book = Recipe.objects.filter(curr_author__in=followed_users)
    r_book = r_book.filter(drink_flag=False).order_by('-time_edited')
    if not r_book:
      errors_f.append('There aint no munch in your stream')
    else:
      for r in r_book:
        (avg_rating,usr_rating) = get_recipe_rating(r, muser)
        if not avg_rating < 0:
          r.avg_rating = avg_rating
        if not usr_rating < 0:
          r.user_rating = usr_rating
        food.append(r)
  except ObjectDoesNotExist:
    errors_f.append('There aint no munch in your stream')
  context = { 'food':food, 'errors_f':errors_f }
  return render(request, 'yum/foodstream.html', context)

@login_required
def drinkstream(request):
  errors_d = []
  drink = []
  muser = MUser.objects.get(id=request.user.id)
  try:
    following_list = list(get_following_set(request.user.id))
    followed_users = MUser.objects.filter(id__in=following_list)
    r_book = Recipe.objects.filter(curr_author__in=followed_users)
    r_book = r_book.filter(drink_flag=True).order_by('-time_edited')
    if not r_book:
      errors_d.append('There aint no drank in your stream')
    else:
      for r in r_book:
        (avg_rating,usr_rating) = get_recipe_rating(r, muser)
        if not avg_rating < 0:
          r.avg_rating = avg_rating
        if not usr_rating < 0:
          r.user_rating = usr_rating
        drink.append(r)
  except ObjectDoesNotExist:
    errors_d.append('There aint no drank in your stream')
  context = { 'drink':drink, 'errors_d':errors_d }
  return render(request, 'yum/drinkstream.html', context)

@login_required
def search_by_name(request):
  # search by recipe name
  context = {}
  user = MUser.objects.get(id=request.user.id);
  if not 'search_term' in request.POST or not request.POST['search_term']:
    return render(request, 'yum/search.html', {'errors':"Oops were you searching for something?"})
  search_name = request.POST['search_term']
  recipes = Recipe.objects.filter(name__contains=search_name)
  recipes = recipes.exclude(is_closed=True);
  if not recipes:
    errors = "There were no recipes found..you should try uploading one"
  errors = []
  context = {'recipes':recipes, 'errors':errors}
  return render(request, 'yum/searchresults.html', context);

@login_required
def search_by_food(request):
  context = {}
  user = MUser.objects.get(id=request.user.id);
  # By ingredient
  if not request.method == 'POST':
    return render(request, 'yum/searchresults.html', context);
  food_list = request.POST.getlist('foodfield');
  col_list = [];
  searchvec = {};
  dictsize = FoodWord.objects.all().count();
  for food in food_list:
    # if food in fooddict
    check = FoodWord.objects.filter(name=food).exists();
    if check:
      col = FoodWord.objects.get(name=food).id;
      col_list.append(col);
      searchvec[col] = 1;
  # Aggregate by row
  rows = Matrix.objects.filter(col__in=col_list).values('row');
  rows = rows.annotate(num_count=Count('col'));
  recipe_ids = [];
  for r in rows:
    recipe_ids.append(r['row']);
  # rank the given list
  recipes = Recipe.objects.filter(id__in=recipe_ids); 
  recipes = recipes.exclude(is_closed=True);
  dictlist = [];
  for r in recipes:
    d = genVector(r.id);
    dictlist.append(d);
  ranklist = getRankList(dictlist,searchvec,dictsize);

  recipe_ids = [];
  for rr in ranklist:
    recipe_ids.append(rr['id']);
  ranked_recipes = [];
  for index in recipe_ids:
    ranked_recipes.append(Recipe.objects.get(id=index))
  context['recipes'] = ranked_recipes;
  return render(request, 'yum/searchresults.html', context)

@login_required
def results_ingredients(request):
  recipes = []
  context = {'recipes':recipes}
  return render(request, 'yum/results_ingredients.html', context)

@login_required
def find_nearest_food(request):
  errors = [];
  context = {};
  context['errors'] = errors;
  try:
    near_food = FoodWord.objects.filter(name__contains=request.POST['text']);
  except:
    traceback.print_exc(file=sys.stdout)
    errors.append('There was an error in the process');
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');
  
  near_food_list = [];
  for food in near_food:
    food_item = {};
    food_item['name'] = food.name;
    food_item['id'] = food.id;
    near_food_list.append(food_item);
    
  context['food_suggestions'] = near_food_list;
  context['success'] = 1;
  json_data = json.dumps(context);
  return HttpResponse(json_data, content_type='application/json');

# Helper function to insert a new food into the food dictionary if no such entry exists
# @foodName the string representing the food
def insert_food(foodName):
  check = FoodWord.objects.filter(name=foodName).exists()
  if not check:
    new_food = FoodWord(name=foodName)
    new_food.save();
  return

@login_required
def recommend_nearest_recipe(request):
  # Given a recipe id, find n nearest recipes
  errors = [];
  context = {};
  context['errors'] = errors;
  if not 'recipe_id' or not request.POST['recipe_id']:
   errors.append('Recipe ID not found');
  
  if len(errors) > 0:
    return render(request, 'yum/searchresults.html', context);
  dictSize = FoodWords.objects.all().count();
  recipe_id = request.POST['recipe_id'];
  searchvec = genVector(recipe_id);
  
  food_list = genFoodList(recipe_id);
  nearby_recipes = genNearbyRecipes(food_list);
  dictlist = [];
  for r in recipes:
    d = genVector(r.id);
    dictlist.append(d);
  ranklist = getRankList(dictlist,searchvec,dictsize);
  recipe_ids = [];
  for rr in ranklist:
    recipe_ids.append(rr['id']);
  ranked_recipes = [];
  for index in recipe_ids:
    ranked_recipes.append(Recipe.objects.get(id=index))
  context['recipes'] = ranked_recipes;
  return render(request, 'yum/searchresults.html', context);

# generate a food dictionary for a given recipe
# @recipe_id recipe id
# returns a python dict:  the key is the food_id and the value is the amt of that particular food
def genVector(recipe_id):
  elements = Matrix.objects.filter(row=recipe_id);
  vdict = {};
  vdict['id'] = recipe_id;
  for e in elements:
    vdict[e.col] = e.value;
  return vdict;

# generates the list of foods used for a given recipe
# @recipe_id recipe id
# returns a list of column number representing the food in the global food dictionary
def genFoodList(recipe_id):
  elements = Matrix.objects.filter(row=recipe_id);
  food_list = [];
  for e in elements:
    food_list.append(e.col);
  return food_list;

# generates the list of neighboring recipes: defined here as any recipe that shares at least
# one ingredient
# @food_list list of column indices representing food
# returns the list of Recipes which are the neighboring recipes
def genNearbyRecipes(food_list):
  rows = Matrix.objects.filter(col__in=food_list).values('row');
  rows = rows.annotate(num_count=Count('col'));
  recipe_ids = [];
  for r in rows:
    recipe_ids.append(r['row']);
  recipes = Recipe.objects.filter(id__in=recipe_ids);
  recipes = recipes.filter(is_closed=True);
  return recipes;

@login_required
def save_recipe(request, id):
  user = MUser.objects.get(id=request.user.id);
  saved_recipe = Recipe.objects.get(id=int(id))
  # generate a deep copy of the recipe for recipebook
  # id=None forces a new record to be made on save() 
  recipe_copy = deepcopy(saved_recipe);
  recipe_copy.id = None;
  recipe_copy.is_closed = True;
  recipe_copy.orig_author = saved_recipe.orig_author + "" + saved_recipe.curr_author.name;
  recipe_copy.curr_author = user;
  recipe_copy.save();
  row_entry = recipe_copy.id;
  food_items = Matrix.objects.filter(row=saved_recipe.id)
  for item in food_items:
    new_elem = Matrix(col=item.col,
                      row=row_entry,
                      value=item.value,
                      metrics=item.metrics)
    new_elem.save();
  return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def show_recipe_editor(request):
  return render(request, 'yum/recipe_editor.html', {})

@login_required
def post_recipe(request):
  # this takes an ajax post and saves recipe to the db 
  # post_recipe view after log in
  errors = [];
  context = {};
  context['errors'] = errors;
  try:
    json_recipe = json.loads(request.POST['recipe']);
    food_list = json_recipe['food_list'];
    for food_item in food_list:
    # first save all the new food items
      insert_food(food_item['name']);
    user = MUser.objects.get(id=request.user.id);
    new_recipe = Recipe(name=request.POST['recipe_name'],
                        orig_author = "",
                        curr_author=user,
                        is_closed=False,
                        drink_flag=bool(int(request.POST['drink_flag'])),
                        serves_num=int(request.POST['serves_num']),
                        instructions=request.POST['instructions']);
    new_recipe.save();

    # new recipes are in the openbook by default
    row_entry = new_recipe.id; 
    # now generate the row vector in the matrix
    for food_item in food_list:
      food_id = FoodWord.objects.get(name=food_item['name']).id;
      new_elem = Matrix(col=food_id,
                        row=row_entry,
                        value=food_item['qty'],
                        metrics=food_item['metrics']);     
      new_elem.save();
  except Exception:
    traceback.print_exc(file=sys.stdout)
    errors.append('There was an error in the process');
  
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');

  context['success'] = 1;
  json_data = json.dumps(context);
  return HttpResponse(json_data, content_type='application/json');

@login_required
def recipe_photo(request):
  recipe = Recipe.objects.filter(curr_author=MUser.objects.get(id=request.user.id))
  recipe = recipe.order_by('-id')[0]
  # page
  if request.POST:
    form = RecipePhotoForm(request.POST, request.FILES, instance=recipe)

    if not form.is_valid():
      context = {'form':form}
      return render(request, 'yum/recipe_photo.html', context)

    form.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
  else:
    form = RecipePhotoForm(instance=recipe)
    context = {'form':form}
    return render(request, 'yum/recipe_photo.html', context)
  context = {'recipe':recipe}
  return render(request, 'yum/recipe_photo.html', context)

# gets picture
@login_required
def recipepic(request):
  recipe = Recipe.objects.filter(curr_author=MUser.objects.get(id=request.user.id))
  recipe = recipe.order_by('-id')[0]
  if not recipe.picture:
    raise Http404

  content_type = guess_type(recipe.picture.name)
  return HttpResponse(recipe.picture, content_type=content_type)

@login_required
def recipe(request, id): 
  not_belong = []
  recipe = Recipe.objects.get(id=int(id)); 
  ingredient = Matrix.objects.filter(row = int(id))
  ingrd = []
  val = []
  unit = []
  for i in ingredient:
    val.append(i.value)
    ingrd.append(FoodWord.objects.get(id=i.col).name)
    unit.append(i.metrics)
  ingredients = zip(val, unit, ingrd)
  if recipe.curr_author != MUser.objects.get(id=request.user.id):
    not_belong.append('NOPE')
  
  suggestions = Suggestion.objects.filter(recipe=recipe)
  suggestions.order_by('-time_edited')
  
  (avg_rating,usr_rating) = get_recipe_rating(recipe, MUser.objects.get(id=request.user.id))
  if not avg_rating < 0:
    recipe.avg_rating = avg_rating
  if not usr_rating < 0:
    recipe.user_rating = usr_rating
  context={}
  context['recipe'] = recipe
  context['ingredients'] = ingredients
  context['not_belong'] = not_belong
  context['suggestions'] = suggestions
  return render(request, 'yum/recipe.html', context)

@login_required
def get_recipe_photo(request,id):
  recipe = Recipe.objects.get(id=int(id))
  if not recipe.picture:
    raise Http404

  content_type = guess_type(recipe.picture.name)
  return HttpResponse(recipe.picture, mimetype=content_type)

@login_required
def delete_recipe(request,id):
  if request.POST:
    recipe = Recipe.objects.get(id=int(id))
    recipe.delete()
    Matrix.objects.filter(row=int(id)).delete()
  return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def recipebook(request):
  errors_f = []
  errors_d = []
  food = []
  drink = []
  muser = MUser.objects.get(id=request.user.id)
  try:
    r_book = Recipe.objects.filter(curr_author=muser)
    if not r_book:
      errors_f.append('There are no recipes in your book')
      errors_d.append('There are no recipes in your book')
    else:
      for r in r_book:
        (avg_rating,usr_rating) = get_recipe_rating(r,muser)
        if not avg_rating < 0:
          r.avg_rating = avg_rating
        if not usr_rating < 0:
          r.user_rating = usr_rating
        if r.drink_flag:
          drink.append(r)
        else:
          food.append(r)
      if not drink:
        errors_d.append('There aint no drank in your book')
      if not food:
        errors_f.append('There aint no munch in your book')
  except ObjectDoesNotExist:
    errors_d.append('There aint no drank in your book')
    errors_f.append('There aint no munch in your book')
  context = { 'food':food, 'drink':drink, 'errors_d':errors_d, 'errors_f':errors_f }
  return render(request, 'yum/recipebook.html', context)

def show_openbook(request,user):
  errors_f = []
  errors_d = []
  food = []
  drink = []
  r_user = MUser.objects.get(id=request.user.id)
  try:
    r_book = Recipe.objects.filter(curr_author=r_user)
    if not r_book:
      errors_f.append('There are no recipes in this openbook')
      errors_d.append('There are no recipes in this openbook')
    else:
      for r in r_book:
        if r.drink_flag:
          drink.append(r)
        else:
          food.append(r)
      if not drink:
        errors_d.append('There aint no drank in this openbook')
      if not food:
        errors_f.append('There aint no munch in this openbook')
  except ObjectDoesNotExist:
    errors_d.append('There aint no drank in this openbook')
    errors_f.append('There aint no munch in this openbook')
  context = {}
  context['food'] = food
  context['drink'] = drink
  context['errors_d'] = errors_d
  context['errors_f'] = errors_f
  context['user'] = r_user
  return render(request, 'yum/openbook.html', context)

@login_required
def edit(request,id):
  recipe = Recipe.objects.get(id=int(id)); 
  if request.POST:
    form = RecipePhotoForm(request.POST, request.FILES, instance=recipe)
    form.save()
  else:
    form = RecipePhotoForm(instance=recipe)

  ingredient = Matrix.objects.filter(row = int(id))
  ingrd = []
  val = []
  unit = []
  for i in ingredient:
    val.append(i.value)
    ingrd.append(FoodWord.objects.get(id=i.col).name)
    unit.append(i.metrics)
  ingredients = zip(val, unit, ingrd)
  context = {'recipe':recipe, 'ingredients':ingredients, 'form':form}
  return render(request, 'yum/edit_recipe.html', context)

@login_required
def save_edit(request):
  # this takes an ajax post and saves recipe to the db 
  # post_recipe view after log in
  errors = [];
  context = {};
  context['errors'] = errors;
  try:
    r_id = request.POST['recipe_id']
    recipe = Recipe.objects.get(id=int(r_id))
    json_recipe = json.loads(request.POST['recipe'])
    food_list = json_recipe['food_list']
    # first save all the new food items
    for food_item in food_list:
      insert_food(food_item['name'])

    user = MUser.objects.get(id=request.user.id);
    recipe.name = request.POST['recipe_name']
    recipe.serves_num=int(request.POST['serves_num'])
    recipe.instructions=request.POST['instructions']
    recipe.save();

    Matrix.objects.filter(row=int(r_id)).delete()
    row_entry = int(r_id)
    # now generate the row vector in the matrix
    for food_item in food_list:
      food_id = FoodWord.objects.get(name=food_item['name']).id;
      new_elem = Matrix(col=food_id,
                        row=row_entry,
                        value=food_item['qty'],
                        metrics=food_item['metrics']);     
      new_elem.save();

  except Exception:
    traceback.print_exc(file=sys.stdout)
    errors.append('There was an error in the process');
  
  if len(errors) > 0:
    context['error'] = 1;
    json_data = json.dumps(context);
    return HttpResponse(json_data, content_type='application/json');

  context['success'] = 1;
  json_data = json.dumps(context);
  return HttpResponse(json_data, content_type='application/json');

@login_required
def suggestion(request, id):
  errors = []
  if not request.method == 'POST':
    errors.append('Not Post')
  if not 'suggestion' in request.POST or not request.POST['suggestion']:
    errors.append('Error in suggestion text')
  if len(errors) > 0:
    return redirect(request.META.get('HTTP_REFERER', '/'))
  recipe = Recipe.objects.get(id=id)
  muser = MUser.objects.get(id=request.user.id)
  text = request.POST['suggestion']
  suggestion = Suggestion(author=muser,
                          recipe=recipe,
                          text=text)
  suggestion.save()
  return redirect(request.META.get('HTTP_REFERER', '/'))
