from __future__ import unicode_literals

import jwt
from django.contrib.auth import get_user_model
from django.utils.encoding import smart_text
from rest_framework import exceptions

from rest_framework.authentication import BaseAuthentication, \
    get_authorization_header

from django.utils.translation import ugettext as _
from django.db import transaction

from rest_framework_services_auth.settings import auth_settings
from rest_framework_services_auth.utils import jwt_decode_token, \
    get_service_user_model, encode_username


class ServiceJSONWebTokenAuthentication(BaseAuthentication):
    """
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string specified in the setting
    `JWT_AUTH_HEADER_PREFIX`. For example:

        Authorization: JWT eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """
    www_authenticate_realm = getattr(auth_settings, 'JWT_REALM', 'api')

    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """
        jwt_value = self.get_jwt_value(request)
        if jwt_value is None:
            return None

        try:
            payload = jwt_decode_token(jwt_value)
            request.jwt_payload = payload
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise exceptions.AuthenticationFailed(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise exceptions.AuthenticationFailed(msg)
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed()

        user = self.authenticate_credentials(payload)

        return (user, jwt_value)

    def get_jwt_value(self, request):
        if auth_settings.JWT_USE_ALTERNATE_AUTH_HEADER:
            return self.get_jwt_value_from_alternate(request)
        else:
            return self.get_jwt_value_from_auth(request) or \
                   self.get_jwt_value_from_alternate(request)

    def get_jwt_value_from_alternate(self, request):
        if auth_settings.JWT_ALTERNATE_AUTH_HEADER_KEY:
            return request.META.get(auth_settings.JWT_ALTERNATE_AUTH_HEADER_KEY)
        else:
            return None

    def get_jwt_value_from_auth(self, request):
        auth = get_authorization_header(request).split()
        auth_header_prefix = auth_settings.JWT_AUTH_HEADER_PREFIX.lower()

        if not auth or smart_text(auth[0].lower()) != auth_header_prefix:
            return None

        if len(auth) == 1:
            msg = _('Invalid Authorization header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid Authorization header. Credentials string '
                    'should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        return auth[1]

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return '{0} realm="{1}"'.format(
            auth_settings.JWT_AUTH_HEADER_PREFIX,
            self.www_authenticate_realm
        )

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        User = get_user_model()
        service_user_id = payload.get('uid', None)

        if not service_user_id:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = get_user_model().objects\
                .get(service_user__pk=service_user_id)
        except User.DoesNotExist:
            service_user = create_service_user(service_user_id)
            user = service_user.user

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user


def create_service_user(service_user_id, ServiceUser=None):
    ServiceUser = ServiceUser or get_service_user_model()
    with transaction.atomic():
        username = encode_username(service_user_id)
        user = get_user_model().objects.create_user(username=username)
        return ServiceUser.objects.create(id=service_user_id, user=user)
