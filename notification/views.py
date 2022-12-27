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



# Create your views here.
class testmedia(APIView):
    serializer_class = TestMediaSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            myfile = serializer.validated_data['media']
            fs = FileSystemStorage(location='dummy_file')  # defaults to   MEDIA_ROOT
            filename = fs.save(myfile.name, myfile)
            # serializer.save()
            task = TestMedia()
            # task.media_field = request.FILES.get('media_field')
            task.save()
            # data1 = request.FILES.get('sample_files')
            t = threading.Thread(target=doCrawl, args=[task.id,myfile.name])
            # t = threading.Thread(target=doCrawl, args=['1',serializer])
            t.setDaemon(True)
            t.start()
            context = {'id':task.id}
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




from django.core.files.images import ImageFile
import os

def doCrawl(id,image):
    task = TestMedia.objects.get(pk=id)
    with open(f'dummy_file/{image}', 'rb') as existing_file:
        django_image_file = ImageFile(file=existing_file, name='filename.jpeg')
        # post = Post(image=django_image_file)
        task.media=django_image_file
        task.is_done=True
        task.save()
        os.remove(f'dummy_file/{image}')
