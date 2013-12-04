from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Count
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
def ownprofile_info(request):
  try:
    if not MUser.objects.filter(id=request.user.id):
      user_name = request.user
      user_info = 'There is currently no other information available'
      MUser(id=request.user.id, name=user_name, info=user_info).save()
    else:
      user_name = MUser.objects.get(id=request.user.id).name
      user_info = MUser.objects.get(id=request.user.id).info
  except ObjectDoesNotExist:
    user_name = request.user
    user_info = 'There is currently no other information available'
    MUser(id=request.user.id, name=user_name, info=user_info).save()
  context = {'name':user_name, 'info':user_info}
  return render(request, 'yum/userprofile.html', context)

@login_required
@transaction.commit_on_success
def edit_profile(request):
    profile_to_edit = MUser.objects.get(id=request.user.id)

    if request.POST:
        form = ProfileForm(request.POST, request.FILES, instance=profile_to_edit)

        if not form.is_valid():
            context = {'form':form}
            return render(request, 'yum/editProfile.html', context)

        form.save()
        return redirect(reverse('ownprofile'))
    else:
        form = ProfileForm(instance=profile_to_edit)
        context = {'form':form}
        return render(request, 'yum/editProfile.html', context)

@login_required
def get_photo(request):
    prof = get_object_or_404(MUser, id=request.user.id)
    if not prof.picture:
        raise Http404

    content_type = guess_type(prof.picture.name)
    return HttpResponse(prof.picture, content_type=content_type)

@login_required
def profile(request, user):
    u = get_object_or_404(MUser, id=request.user.id)
    user_name = u
    user_info = u.info
    context = {'name' : user_name, 'info' : user_info}
    return render(request, 'yum/profile.html', context)

@login_required
def get_prof_photo(request, user):
    u = get_object_or_404(MUser, id=request.user.id)
    if not u:
        raise Http404

    if not u.picture:
        raise Http404

    content_type = guess_type(u.picture.name)
    return HttpResponse(u.picture, mimetype=content_type)
