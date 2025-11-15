from .auth_utils import send_otp_request, get_token_request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginKhakpourViewSerializer, VerifyOtpKhakpourViewSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(
        request=LoginKhakpourViewSerializer,
        tags=['Admin Pannel (user)']
    )
class LoginKhakpourView(APIView):
 
    def post(self, request):
        serdata = LoginKhakpourViewSerializer(data=request.data)
        if serdata.is_valid():
            phone_number = serdata.validated_data['phone_number']
            otp_response = send_otp_request(phone_number)
            if otp_response.get('success'):
                return Response(
                    {'message': 'OTP sent successfully'}, 
                    status=status.HTTP_200_OK
                )
            else:
                response_data = otp_response.get('data', {'error': 'Failed to send OTP'})
                response_status = otp_response.get('status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                if response_status == 422:
                    return Response(
                        response_data, 
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY # یا 400
                    )
                
                return Response(
                    {'error': 'Failed to send OTP due to external API error', 'details': response_data}, 
                    status=response_status
                )
        
        else:
            return Response(serdata.errors, status=status.HTTP_400_BAD_REQUEST)









@extend_schema(
        request=VerifyOtpKhakpourViewSerializer,
        tags=['Admin Pannel (user)'],
    )
class VerifyOtpKhakpourView(APIView):
    

    def post(self, request):
        serdata = VerifyOtpKhakpourViewSerializer(data=request.data)
        
        if serdata.is_valid():
            phone_number = serdata.validated_data['phone_number']
            otp_code = serdata.validated_data['otp_code']
            
            token_response = get_token_request(phone_number, otp_code)
            
            if token_response.get('token'):
                
                token = token_response['token']
                
                response = Response(
                    {'message': 'Authentication successful', 'token':token}, 
                    status=status.HTTP_200_OK
                )
                return response
            
            else:
                error_content = token_response.get('error', {'message': 'Unknown external API error'})
                status_code_http = token_response.get('status_code', status.HTTP_400_BAD_REQUEST)
                
                if isinstance(error_content, dict):
                    return Response(error_content, status=status_code_http)
                
                return Response(
                    {'error': error_content}, 
                    status=status_code_http
                )

        else:
            return Response(serdata.errors, status=status.HTTP_400_BAD_REQUEST)