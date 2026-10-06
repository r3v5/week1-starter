from django.shortcuts import render

def map_view(request):
    context = {
        'dublin_lat': 53.3498,
        'dublin_lon': -6.2603,
    }
    return render(request, 'mapping/map.html', context)
