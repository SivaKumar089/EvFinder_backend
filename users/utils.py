from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_otp_email(user, otp):
    subject = "EVLocate - Email Verification Code"
    message = render_to_string('../templates/reset_password_email.html', {
        'username': user.username,
        'otp': otp,
    })
    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [user.email])
    email.content_subtype = "html"
    email.send()
