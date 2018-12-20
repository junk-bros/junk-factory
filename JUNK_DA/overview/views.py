from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
def test(request):
    return HttpResponse('123')