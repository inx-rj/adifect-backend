from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import TestMediaSerializer
from .models import TestMedia
import threading
from rest_framework.response import Response
from rest_framework import status
import base64
import io
from io import TextIOWrapper


# Create your views here.
class testmedia(APIView):
    serializer_class = TestMediaSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            task = TestMedia()
            # task.media_field = request.FILES.get('media_field')
            task.save()
            data1 = request.FILES.get('sample_files')
            t = threading.Thread(target=doCrawl, args=[task.id,request])
            t.setDaemon(True)
            t.start()
            context = {'id': task.id}
            # return JsonResponse({'id': task.id})
            return Response(context, status=status.HTTP_200_OK)
        return Response({"message":"error"})


# def startCrawl(request):
class get_media(APIView):
    def get(self, request,id):
        # id = request.GET.get('id', None)
        # print('id')
        # print(id)
        # print(args.get('id'))
        task = TestMedia.objects.get(pk=id)
        context = {'is_done': task.is_done, 'result': task.media_field}
        # return JsonResponse({'id': task.id})
        return Response(context, status=status.HTTP_200_OK)


#
# def checkCrawl(request,id):
#     task = Crawl.objects.get(pk=id)
#     return JsonResponse({'is_done':task.is_done, result:task.result})

from io import TextIOWrapper
def clean_myfilefield(request):
    # file = self.cleaned_data['myfilefield']
    print("llll")
    new = request.FILES.getlist('sample_files', None)[0]
    read_file = TextIOWrapper(new, encoding='ASCII')
    headerCounter = 0
    for line in read_file:
        if ">" in line:
            headerCounter += 1
    if headerCounter > 1:
        error = "Custom error message 1"
        # raise ValidationError(error)
    if headerCounter == 0:
        error = "Custom error message 2"
        # raise ValidationError(error)
    read_file.detach()
    return new

def doCrawl(id,request):
    print("innnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
    task = TestMedia.objects.get(pk=id)
    # new = request.FILES.getlist('sample_files', None)
    # for i in new:
    task.title = request.data.get('title')
    task.media = request.FILES.getlist('sample_files', None)[0]
    task.save()

    # print(task.media)
    print("enddddddddddddddddddddddddddddddddddddddd")
    task.save()
