import os

from django.views import generic
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


class MailHelper(generic.View):
    def mail_send(context, subject, to, sender_mail):
        html_content = context
        msg = EmailMultiAlternatives(subject=subject, from_email='Team ' + settings.SITE_NAME +'<' + sender_mail + '>',
                                     to=[to, 'workspaceinfotech@gmail.com'], body=html_content)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

