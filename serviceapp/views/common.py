import base64
import json
import os
import random
import string

from PIL import Image
from django.views import generic
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from serviceapp.views.helper import LogHelper
from serviceapp.views.mail import MailHelper
import threading


class CommonView(generic.DetailView):

    # def send_verification_code(request, to, verification_code):
    #     response = {}
    #     try:
    #         body = "Verification Code - " + str(verification_code)
    #         subject = "Account Verification Code"
    #         sender_mail = settings.EMAIL_HOST_USER
    #         task = threading.Thread(target=MailHelper.mail_send, args=(body, subject, to, sender_mail))
    #         task.start()
    #         response['success'] = True
    #     except Exception as e:
    #         LogHelper.elog(e)
    #         response['success'] = False
    #     return HttpResponse(json.dumps(response), content_type='application/json')

    # Imaginary function to handle an uploaded file.
    def handle_uploaded_file(f, user=None):
        try:
            try:
                os.makedirs(os.path.join(settings.MEDIA_ROOT, "avatar"))
            except FileExistsError:
                # directory already exists
                pass
            random_number = CommonView.randomString(10)
            file = str(f.name).rsplit('.', 1)
            if user:
                filename = user.first_name + "_" + random_number + "." + file[1]
                thumb_filename = user.first_name + "_" + random_number + "_thumb." + file[1]
            else:
                filename = file[0] + "_" + random_number + "." + file[1]
                thumb_filename = file[0] + "_" + random_number + "_thumb." + file[1]
            full_filename = os.path.join(settings.MEDIA_ROOT, "avatar", filename)
            thumb_full_filename = os.path.join(settings.MEDIA_ROOT, "avatar", thumb_filename)
            fout = open(full_filename, 'wb+')
            # host_url = "http://"+request.get_host()
            host_url = ""
            for chunk in f.chunks():
                fout.write(chunk)
            fout.close()
            if user:
                try:
                    user.avatar.delete(False)
                    user.avatar_thumb.delete(False)
                except Exception as e:
                    print(e)
            with open(full_filename, 'r+b') as f:
                with Image.open(f) as image:
                    image.thumbnail((150, 150))
                    image.save(thumb_full_filename, optimize=True, quality=40)
            file_info = {
                "path": host_url + "avatar/" + filename,
                "thumb_path": host_url + "avatar/" + thumb_filename,
            }
            return file_info
        except Exception as e:
            LogHelper.efail(e)
            return ""

    def get_file_path(file):
        file = str(file)
        print()
        file_path = ""
        try:
            file_path = settings.MEDIA_URL+file
        except Exception as e:
            LogHelper.elog(e)
        return file_path

    # This function is used for create a random string which we need in upload files name
    def randomString(stringLength=10):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    def make_base64(request, text):
        message = text
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return base64_message
