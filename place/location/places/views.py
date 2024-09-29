from django.shortcuts import render, redirect
from .models import Place
import pandas as pd
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.db.models import Q

def get_all_children(place_id):
    """Recursively get all children of a place"""
    place = Place.objects.get(id=place_id)
    children = list(Place.objects.filter(parent=place))
    for child in children:
        children.extend(get_all_children(child.id))
    return children

def place_view(request):
    if request.method == 'POST':
        if 'upload' in request.POST:
            excel_file = request.FILES.get('excel_file')

            if excel_file:
                try:
                    # Read Excel file, assuming first row is header
                    df = pd.read_excel(excel_file)
                    
                    for _, row in df.iterrows():
                        try:
                            place_id = int(row['id'])
                            place_name = str(row['place_name'])
                            parent_id = row['parent_id']

                            parent = None
                            if pd.notna(parent_id):
                                parent, _ = Place.objects.get_or_create(id=int(parent_id))

                            Place.objects.update_or_create(
                                id=place_id,
                                defaults={
                                    'place_name': place_name,
                                    'parent': parent
                                }
                            )
                        except ValueError as ve:
                            messages.warning(request, f"Skipped row due to invalid data: {row.to_dict()}. Error: {str(ve)}")
                        except Exception as e:
                            messages.warning(request, f"Error processing row: {row.to_dict()}. Error: {str(e)}")

                    messages.success(request, 'Excel data uploaded successfully.')
                except Exception as e:
                    messages.error(request, f'Error uploading Excel data: {str(e)}')
            else:
                messages.error(request, 'Please select an Excel file to upload.')

        elif 'export' in request.POST:
            export_type = request.POST.get('export_type', 'default')
            
            if export_type == 'default':
                places = Place.objects.all().order_by('id')
            else:  # custom export
                selected_place_ids = request.POST.getlist('selected_places')
                places = set()
                for place_id in selected_place_ids:
                    places.add(Place.objects.get(id=place_id))
                    places.update(get_all_children(place_id))
                places = sorted(list(places), key=lambda x: x.id)
            
            if not places:
                messages.error(request, 'No places selected for export.')
                return redirect('place_view')
            
            data = {
                'id': [place.id for place in places],
                'place_name': [place.place_name for place in places],
                'parent_id': [place.parent.id if place.parent else None for place in places]
            }
            df = pd.DataFrame(data)
            
            # Create an Excel file
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=places_export.xlsx'
            
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Places')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return response
            else:
                return render(request, 'place_view.html', {'places': places})

    # Fetch the updated list of places after processing the POST request
    places = Place.objects.all().order_by('id')
    return render(request, 'place_view.html', {'places': places})
