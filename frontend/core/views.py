from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "core/base.html")


def styling(request):
    return render(request, "core/styling.html")

def styling2(request):
    ships = [
        (3514, "Revenant"),
        (42125, "Vendetta"),
        (3764, "Leviathan"),
        (23773, "Ragnarok")
    ]
    characters = [
        (93417038, "Capri Sun KraftFoods"),
        (92060039, "Braxus Deninard"),
        (1674115962, "joecuster"),
        (443630591, "The Mittani")
    ]
    return render(request, "core/styling2.html", {"ships": ships, "characters": characters})