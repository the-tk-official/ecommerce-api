from datetime import datetime

import jwt
from django.conf import settings


class TokenManager:
    """Token Manager"""
    @staticmethod
    def get_token(exp, payload, token_type='access'):
        """Creating token from the input data"""
        exp = datetime.now().timestamp() + (exp * 60)

        return jwt.encode(
            {'exp': exp, 'token_type': token_type, **payload},
            settings.SECRET_KEY,
            algorithm='HS256'
        )

    @staticmethod
    def decode_token(token):
        """Decoding data from the input token"""
        try:
            decoded = jwt.decode(token, key=settings.SECRET_KEY, algorithms='HS256')
        except jwt.DecodeError:
            return None

        if datetime.now().timestamp() > decoded['exp']:
            return None

        return decoded

    @staticmethod
    def get_access_token(payload):
        """Creating access token from the input data"""
        return TokenManager.get_token(exp=5, payload=payload, token_type='access')

    @staticmethod
    def get_refresh_token(payload):
        """Creating refresh token from the input data"""
        return TokenManager.get_token(exp=7*24*60, payload=payload, token_type='refresh')


class Authentication:
    """Authentication"""
    def __init__(self, request):
        self.request = request

    def authenticate(self):
        """User authentication"""
        data = self.validate_request()

        if not data:
            return None

        return self.get_user(data['user_id'])

    def validate_request(self):
        """Validate input data from request for authentication"""
        authorization = self.request.headers.get('AUTHORIZATION', None)

        if not authorization:
            return None

        token = authorization[4:]
        decoded_data = TokenManager.decode_token(token=token)

        if not decoded_data:
            return None

        return decoded_data

    @staticmethod
    def get_user(user_id):
        """Find user from db and return obj"""
        from user.models import User

        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None
