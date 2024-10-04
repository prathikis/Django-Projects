from django.shortcuts import render, redirect
from .models import Place
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import logging
from django.views.decorators.http import require_GET
from openpyxl import Workbook, load_workbook
import json


def get_all_children(place_id):
    children = list(Place.objects.filter(parent_id=place_id))
    for child in children:
        children.extend(get_all_children(child.id)) #recursivly adding the children to the
    return children

def build_place_hierarchy(places):
    hierarchy = []
    place_dict = {place.id: {'place': place, 'children': []} for place in places}
    
    for place in places:
        if place.parent_id is None:
            hierarchy.append(place_dict[place.id])
        else:
            place_dict[place.parent_id]['children'].append(place_dict[place.id])
    
    return hierarchy

def get_all_descendants(place):
    descendants = []
    children = Place.objects.filter(parent=place)
    for child in children:
        descendants.append(child)
        descendants.extend(get_all_descendants(child))
    return descendants


def place_view(request):
    if request.method == 'POST' and 'export' in request.POST:
        export_type = request.POST.get('export_type')
        
        # Create a new workbook and add a worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Places"

        places_to_export = []

        if export_type == 'selected':
            selected_state = json.loads(request.POST.get('selected_state', '{}'))
            selected_district = json.loads(request.POST.get('selected_district', '{}'))
            selected_taluk = json.loads(request.POST.get('selected_taluk', '{}'))

            if selected_taluk:
                places_to_export = [Place.objects.get(id=selected_taluk['id'])]
            elif selected_district:
                places_to_export = Place.objects.filter(parent_id=selected_district['id'])
            elif selected_state:
                district_ids = Place.objects.filter(parent_id=selected_state['id']).values_list('id', flat=True)
                places_to_export = Place.objects.filter(parent_id__in=district_ids)
        else:
            # Get all places
            places_to_export = Place.objects.filter(parent__parent__isnull=False)

        for place in places_to_export:
            hierarchy = get_place_hierarchy_list(place)
            ws.append(hierarchy)

        # Create the HttpResponse object with Excel mime type
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=places_export.xlsx'

        # Save the workbook to the response
        wb.save(response)

        return response

    # For GET requests, render the template
    return render(request, 'place_view.html')

@require_GET
def get_place_hierarchy(request):
    def get_children(parent):
        children = Place.objects.filter(parent=parent)
        return [
            {
                'id': child.id,
                'name': child.place_name,
                'children': get_children(child)
            }
            for child in children
        ]

    root_places = Place.objects.filter(parent=None)
    hierarchy = [
        {
            'id': place.id,
            'name': place.place_name,
            'children': get_children(place)
        }
        for place in root_places
    ]

    return JsonResponse(hierarchy, safe=False)

def get_place_hierarchy_list(place):
    hierarchy = [place.place_name]
    current = place.parent
    while current:
        hierarchy.insert(0, current.place_name)
        current = current.parent
    return hierarchy[:3]  # Return only State, District, Taluk

def get_full_hierarchy(place):
    hierarchy = [place.place_name]
    current = place.parent
    while current:
        hierarchy.insert(0, current.place_name)
        current = current.parent
    return ' ➞  '.join(hierarchy)
