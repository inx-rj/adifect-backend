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
from django.core.files.storage import FileSystemStorage
from django.core.files.images import ImageFile
from django.core.files import storage
from django.core.files.images import ImageFile
import os


# Create your views here.
class testmedia(APIView):
    serializer_class = TestMediaSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            myfile = serializer.validated_data['media']
            # fs = FileSystemStorage(location='dummy_file')  # defaults to   MEDIA_ROOT
            # filename = fs.save(myfile.name, myfile)
            task = TestMedia()
            task.save()
            fs = FileSystemStorage(location='dummy_file/')  # defaults to   MEDIA_ROOT
            filename = fs.save(myfile.name, myfile)
            # file_url = fs.url(filename)
            # print(file_url)
            t = threading.Thread(target=doCrawl, args=[task.id,myfile.name])
            # t = threading.Thread(target=doCrawl, args=[task.id,request.FILES['media']])
            print("error")
            t.setDaemon(True)
            t.start()
            context = {'id':task.id}
            # return JsonResponse({'id': task.id})
            print("done")
            return Response(context, status=status.HTTP_200_OK)
        return Response({"message":"error","error":serializer.errors})


# def startCrawl(request):
class get_media(APIView):
    def get(self, request,id):
        # id = request.GET.get('id', None)
        # print('id')
        # print(id)
        # print(args.get('id'))
        task = TestMedia.objects.get(pk=id)
        if task.is_done:
            result = task.media.url
        else:
            result = ''
        context = {'is_done': task.is_done, 'result':result}
        # return JsonResponse({'id': task.id})
        return Response(context, status=status.HTTP_200_OK)


from django.core.files.storage import default_storage


def doCrawl(id,myfile):
    task = TestMedia.objects.get(pk=id)

    '''
    with open(f'dummy_file/{image}', 'rb') as existing_file:
        django_image_file = ImageFile(file=existing_file, name='filename.jpeg')
        # post = Post(image=django_image_file)
        task.media=django_image_file
        task.is_done=True
        task.save()
    '''

    print('task_start')
    # myfile = image

    # print(myfile)
    # print(type(myfile))
    # # print(1+'1')
    # fs = FileSystemStorage(location='dummy_file/')
    # print("____hitt____")
    # print(myfile.name)
    #
    # # defaults to   MEDIA_ROOT
    # filename = fs.save(myfile.name, myfile)
    # print(filename)
    with open(f'dummy_file/{myfile}', 'rb') as existing_file:
        django_image_file = storage.File(file=existing_file, name=myfile)
        task.media = django_image_file
        task.is_done = True
        task.save()
    print("end")
    os.remove(f'dummy_file/{myfile}')
