import os
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET
from django.http import FileResponse, Http404, HttpResponseNotFound, JsonResponse

def index_view(request):

    if request.user.is_authenticated:
        # has a logged-in user
        if(request.user.account_type == "teacher"):
            return redirect("teachers_menu")
        elif(request.user.account_type == "student"):
            return redirect("students_menu")
    else:
        # anonymous
        return render(request, "../templates/index.html")
    

@require_GET
def get_brochure_file(request):
    # build paths
    path_to_file = os.path.join(os.path.join(default_storage.location, 'product', 'Sahayak_Writer_Brouchure.png'))

    if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
        return FileResponse(open(path_to_file, "rb"), content_type="image/png", as_attachment=True, filename="Sahayak_Writer_Brouchure.png")
    else:
        return render(request, "404.html")
    
@require_GET
def get_demo_video(request):
    # build paths
    path_to_file = os.path.join(os.path.join(default_storage.location, 'product', 'Sahayak_Writer_with_subs.mp4'))

    if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
        return FileResponse(open(path_to_file, "rb"), content_type="video/mp4", filename="Sahayak_Writer_Demo.mp4")
    else:
        return render(request, "404.html")