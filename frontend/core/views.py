from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "core/base.html")


def styling(request):
    return render(request, "core/styling.html")