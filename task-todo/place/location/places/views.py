from django.shortcuts import render, redirect
from .models import Place
import pandas as pd
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
import logging
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)
def get_all_children(place_id):
    children = list(Place.objects.filter(parent_id=place_id))
    for child in children:
        children.extend(get_all_children(child.id))
    return children

def get_place_hierarchy(places):
    hierarchy = []
    place_dict = {place.id: {'place': place, 'children': []} for place in places}
    
    for place in places:
        if place.parent_id is None:
            hierarchy.append(place_dict[place.id])
        else:
            place_dict[place.parent_id]['children'].append(place_dict[place.id])
    
    return hierarchy

def place_view(request):
    if request.method == 'POST':
        if 'upload' in request.POST:
            excel_file = request.FILES.get('excel_file')

            if excel_file:
                try:
                    df = pd.read_excel(excel_file, header=None)
                    #if any fail in the process it undos the other process and consider a single block of code
                    with transaction.atomic(): 
                        for _, row in df.iterrows():
                            try:
                                place_id = int(row[0]) 
                                place_name = str(row[1])  
                                parent_id = row[2]  

                                parent = None
                                if pd.notna(parent_id):
                                    parent, _ = Place.objects.get_or_create(id=int(parent_id))

                                place, created = Place.objects.update_or_create(
                                    id=place_id,
                                    defaults={
                                        'place_name': place_name,
                                        'parent': parent
                                    }
                                )
                                
                                if created:
                                    logger.info(f"Created new place: {place}")
                                else:
                                    logger.info(f"Updated existing place: {place}")

                            except Exception as e:
                                logger.error(f"Error processing row:{e}")

                    messages.success(request, 'Excel data uploaded successfully.')
                except Exception as e:
                    logger.error(f"Error uploading Excel data:{e}")
                    messages.error(request, 'An error occurred while uploading the Excel data.')
            else:#excel file not selected means
                messages.error(request, 'Please select an Excel file to upload.')

        elif 'export' in request.POST:
            export_type = request.POST.get('export_type', 'default')
            include_headers = True  # You can make this configurable if needed
            
            if export_type == 'default':
                places = Place.objects.all().order_by('id')
            else:  # 'selected'
                selected_place_ids = request.POST.getlist('selected_places')
                if not selected_place_ids:
                    messages.error(request, 'No places selected for export.')
                    return redirect('places:place_view')
                
                places = Place.objects.filter(id__in=selected_place_ids).order_by('id')
                all_places = set(places)
                for place in places:
                    all_places.update(get_all_children(place.id))
                places = sorted(all_places, key=lambda x: x.id)
            
            if not places:
                messages.error(request, 'No places available for export.')
                return redirect('places:place_view')
            
            data = {
                'id': [place.id for place in places],
                'place_name': [place.place_name for place in places],
                'parent_id': [place.parent.id if place.parent else 'null' for place in places],
            }
            df = pd.DataFrame(data)
            df = df.replace(r'^\s*$', 'null', regex=True)
            
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=places_export.xlsx'
            
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                if include_headers:
                    df.to_excel(writer, index=False, sheet_name='Places')
                else:
                    df.to_excel(writer, index=False, sheet_name='Places', header=False)
            
            return response

        elif 'export_headers' in request.POST:
            # only headers excel file for uploading the data
            data = {
                'id': [],
                'place_name': [],
                'parent_id': [],
            }
            df = pd.DataFrame(data)
            
            # excel file creating
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=places_template.xlsx'
            
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='template')
            
            return response

    places = Place.objects.all().order_by('id')
    place_hierarchy = get_place_hierarchy(places)
    return render(request, 'place_view.html', {'places': places, 'place_hierarchy': place_hierarchy})

@require_POST
def toggle_all_places(request):
    select_all = request.POST.get('select_all') == 'true'
    if select_all:
        place_ids = list(Place.objects.values_list('id', flat=True))
    else:
        place_ids = []
    return JsonResponse({'place_ids': place_ids})
