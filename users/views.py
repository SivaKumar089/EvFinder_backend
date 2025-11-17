from rest_framework.permissions import AllowAny
from rest_framework import status, permissions, views, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from random import randint
import random

from .models import Users, SignupOTP, EmailOTP
from .serializers import (
    UserSerializer,
    LoginSerializer,
    ProfileSerializer,
    SignupOTPSerializer
)
from .utils import send_otp_email


# 🧍‍♂️ User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


from rest_framework import permissions, status, views
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings
from .models import SignupOTP
import random

class SignupSendOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)


        if Users.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete any old OTPs for same email
        SignupOTP.objects.filter(email=email).delete()



        # Generate new OTP
        code = str(random.randint(1000, 9999))
        otp_record = SignupOTP.objects.create(email=email, code=code)

        # Send email
        html_template = get_template("signup_otp.html")
        html_content = html_template.render({"otp": code, "username": email.split("@")[0]})

        subject = "EVLocate Signup OTP"
        from_email = settings.EMAIL_HOST_USER
        to_email = [email]

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=f"Your EVLocate signup OTP is {code}",
            from_email=from_email,
            to=to_email,
        )
        email_message.attach_alternative(html_content, "text/html")
        try:
            email_message.send(fail_silently=False)
        except Exception as e:
            return Response({"error": "Failed to send email", "details": str(e)}, status=500)

        return Response({"message": "OTP sent successfully", "email": email}, status=status.HTTP_200_OK)




from django.utils import timezone
from datetime import timedelta

from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import pytz
from .models import SignupOTP

from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import SignupOTP
import random

from django.utils import timezone
from datetime import timedelta
from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import SignupOTP
import pytz

class SignupVerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "Email and OTP code are required"}, status=status.HTTP_400_BAD_REQUEST)

        otp_record = SignupOTP.objects.filter(email=email).order_by('-created_at').first()
        if not otp_record:
            return Response({"error": "No OTP found for this email"}, status=status.HTTP_404_NOT_FOUND)
        print(code,type(code))
        print(otp_record.code,type(otp_record.code))
        print("Created (IST):", otp_record.created_at.astimezone(pytz.timezone('Asia/Kolkata')))
        print("Now (IST):", timezone.now().astimezone(pytz.timezone('Asia/Kolkata')))

        if otp_record.is_expired():
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
        
        if int(otp_record.code) != int(code):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        otp_record.is_verified = True
        otp_record.save()

        return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['email_or_username']
            password = serializer.validated_data['password']

            try:
                user = Users.objects.get(Q(email=identifier) | Q(username=identifier))
            except Users.DoesNotExist:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            if not check_password(password, user.password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                return Response({"error": "Account is inactive"}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": ProfileSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🚪 Logout View
class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token or already logged out"}, status=status.HTTP_400_BAD_REQUEST)


# 🔁 Send OTP for existing users (e.g., forgot password)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_otp(request):
    email = request.data.get("email")
    try:
        user = Users.objects.get(email=email)
        otp = str(randint(1000, 9999))

        EmailOTP.objects.filter(user=user).delete()
        EmailOTP.objects.create(user=user, otp=otp)
        send_otp_email(user, otp)
        return Response({"message": "OTP sent successfully to your email."}, status=200)
    except Users.DoesNotExist:
        return Response({"error": "User not found."}, status=404)


# 🔍 Verify OTP for existing users
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("code")

    try:
        user = Users.objects.get(email=email)
        record = EmailOTP.objects.filter(user=user, otp=otp).latest('created_at')

        if record.is_expired():
            return Response({"error": "OTP expired. Please request a new one."}, status=400)

        user.is_verified = True
        user.save()
        record.delete()
        return Response({"message": "Email verified successfully!"}, status=200)

    except EmailOTP.DoesNotExist:
        return Response({"error": "Invalid OTP"}, status=400)
    except Users.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


@api_view(['PUT'])
def forgot_password(request):
    email = request.data.get("email")
    new_password = request.data.get("new_password")

    if not email or not new_password:
        return Response({"error": "Email and new password required"}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Check OTP verification first
    otp_record = SignupOTP.objects.filter(email=email).last()
    if not otp_record:
        return Response({"error": "OTP not verified for this email"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Users.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp_record.is_verified = False
        otp_record.save()

        return Response({"message": "Password reset successfully!"}, status=status.HTTP_200_OK)

    except Users.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)