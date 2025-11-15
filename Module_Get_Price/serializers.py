from rest_framework import serializers

class LoginKhakpourViewSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyOtpKhakpourViewSerializer(serializers.Serializer): 
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=6)