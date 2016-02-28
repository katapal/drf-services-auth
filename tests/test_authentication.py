from uuid import uuid4

from django.conf import settings
from django.conf.urls import patterns
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from rest_framework import permissions, status
from rest_framework.test import APIRequestFactory, APIClient, APITestCase
from rest_framework.views import APIView
from rest_framework_services_auth.authentication import \
    DynamicJSONWebTokenAuthentication
from rest_framework_services_auth.models import DynamicUser
from rest_framework_services_auth.utils import jwt_encode_user, jwt_encode_uid

User = get_user_model()

factory = APIRequestFactory()

DEFAULT_TARGET = {
    'SECRET_KEY': settings.JWT_VERIFICATION_KEY, # assume a sym key for test
    'ALGORITHM': settings.JWT_ALGORITHM,
    'AUDIENCE': settings.JWT_AUDIENCE
}

class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


urlpatterns = patterns(
    '',
    (r'^jwt/$', MockView.as_view(
     authentication_classes=[DynamicJSONWebTokenAuthentication])),
)


class DynamicJSONWebTokenAuthenticationTests(APITestCase):
    """JSON Web Token Authentication"""
    urls = 'tests.test_authentication'

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'jpueblo'
        self.email = 'jpueblo@example.com'
        self.user = User.objects.create_user(self.username, self.email)
        DynamicUser.objects.create(user=self.user)

    def test_post_form_passing_jwt_auth(self):
        """
        Ensure POSTing form over JWT auth with correct credentials
        passes and does not require CSRF
        """
        token = jwt_encode_user(self.user, DEFAULT_TARGET)

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(dynamic_user__id=self.user.dynamic_user.id)
        self.assertEqual(user.dynamic_user.id, self.user.dynamic_user.id)
        self.assertEqual(user.username, self.user.username)

    def test_post_json_passing_jwt_auth(self):
        """
        Ensure POSTing JSON over JWT auth with correct credentials
        passes and does not require CSRF
        """
        token = jwt_encode_user(self.user, DEFAULT_TARGET)

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(dynamic_user__id=self.user.dynamic_user.id)
        self.assertEqual(user.dynamic_user.id, self.user.dynamic_user.id)
        self.assertEqual(user.username, self.user.username)

    def test_post_form_passing_jwt_auth_new_user(self):
        """
        Ensure POSTing form over JWT auth with correct credentials
        passes and does not require CSRF
        """
        uid = str(uuid4())
        token = jwt_encode_uid(uid, DEFAULT_TARGET)

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(dynamic_user__id=uid)
        self.assertEqual(str(user.dynamic_user.id), uid)
        self.assertEqual(user.username, str(uid))

    def test_post_json_passing_jwt_auth_new_user(self):
        """
        Ensure POSTing JSON over JWT auth with correct credentials
        passes and does not require CSRF
        """
        uid = str(uuid4())
        token = jwt_encode_uid(uid, DEFAULT_TARGET)

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(dynamic_user__id=uid)
        self.assertEqual(str(user.dynamic_user.id), uid)
        self.assertEqual(user.username, str(uid))

    def test_post_form_failing_jwt_auth(self):
        """
        Ensure POSTing form over JWT auth without correct credentials fails
        """
        response = self.csrf_client.post('/jwt/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_json_failing_jwt_auth(self):
        """
        Ensure POSTing json over JWT auth without correct credentials fails
        """
        response = self.csrf_client.post('/jwt/', {'example': 'example'},
                                         format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_no_jwt_header_failing_jwt_auth(self):
        """
        Ensure POSTing over JWT auth without credentials fails
        """
        auth = 'JWT'
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        msg = 'Invalid Authorization header. No credentials provided.'

        self.assertEqual(response.data['detail'], msg)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_invalid_jwt_header_failing_jwt_auth(self):
        """
        Ensure POSTing over JWT auth without correct credentials fails
        """
        auth = 'JWT abc abc'
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        msg = ('Invalid Authorization header. Credentials string '
               'should not contain spaces.')

        self.assertEqual(response.data['detail'], msg)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_expired_token_failing_jwt_auth(self):
        """
        Ensure POSTing over JWT auth with expired token fails
        """
        token = jwt_encode_user(self.user, DEFAULT_TARGET, override={'exp': 1})

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        msg = 'Signature has expired.'

        self.assertEqual(response.data['detail'], msg)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_invalid_token_failing_jwt_auth(self):
        """
        Ensure POSTing over JWT auth with invalid token fails
        """
        auth = 'JWT abc123'
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        msg = 'Error decoding signature.'

        self.assertEqual(response.data['detail'], msg)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'JWT realm="api"')

    def test_post_form_passing_jwt_invalid_payload(self):
        """
        Ensure POSTing json over JWT auth with invalid payload fails
        """
        token = jwt_encode_user(self.user,
                                DEFAULT_TARGET,
                                override={'aud': 'asldkfjalskdjf'})

        auth = 'JWT {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)

        msg = 'Incorrect authentication credentials.'

        self.assertEqual(response.data['detail'], msg)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_different_auth_header_prefix(self):
        """
        Ensure using a different setting for `JWT_AUTH_HEADER_PREFIX` and
        with correct credentials passes.
        """
        settings.JWT_AUTH_HEADER_PREFIX = 'Bearer'

        token = jwt_encode_user(self.user, DEFAULT_TARGET)

        auth = 'Bearer {0}'.format(token)
        response = self.csrf_client.post(
            '/jwt/', {'example': 'example'},
            HTTP_AUTHORIZATION=auth, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Restore original settings
        settings.JWT_AUTH_HEADER_PREFIX = 'JWT'

    def test_post_form_failing_jwt_auth_different_auth_header_prefix(self):
        """
        Ensure using a different setting for `JWT_AUTH_HEADER_PREFIX` and
        POSTing form over JWT auth without correct credentials fails and
        generated correct WWW-Authenticate header
        """
        settings.JWT_AUTH_HEADER_PREFIX = 'Bearer'

        response = self.csrf_client.post('/jwt/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'Bearer realm="api"')

        # Restore original settings
        settings.JWT_AUTH_HEADER_PREFIX = 'JWT'
