import json
from datetime import datetime
from time import sleep
from unittest import mock

from django.test import TestCase, override_settings
from freezegun import freeze_time
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token
from graphql_jwt.utils import get_payload

from apps.pku_auth.backends import OpenIDClientBackend
from apps.pku_auth.models import OpenIDClient
from apps.user.models import User, Department


class BackendTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        OpenIDClient.objects.create(client_id='id1',
                                    client_secret='password1',
                                    authorization_endpoint='http://some.com/1',
                                    token_endpoint='http://some.com/1',
                                    userinfo_endpoint='http://some.com/1',
                                    redirect_uri='http://localhost/1',
                                    scopes='openid profile email')
        OpenIDClient.objects.create(client_id='123',
                                    client_secret='password',
                                    authorization_endpoint='http://some.com/',
                                    token_endpoint='http://some.com/',
                                    userinfo_endpoint='http://some.com/',
                                    redirect_uri='http://localhost/',
                                    scopes='openid profile')
        cls.department = Department.objects.create(department='some-department')
        cls.user = User.objects.create(pku_id='2000000000', department=cls.department)

    def test_authenticate_no_create(self):
        backend = OpenIDClientBackend()
        get_token = mock.Mock(return_value='123')
        with mock.patch.object(backend, 'get_token', get_token):
            userinfo = mock.Mock(return_value={
                'is_pku': True,
                'pku_id': '2000000000',
                'department': 'some-department'
            })
            with mock.patch.object(backend, 'get_userinfo', userinfo):
                user = backend.authenticate(None, '123')
                self.assertEqual(user, self.user)

    def test_authenticate_no_pku(self):
        backend = OpenIDClientBackend()
        get_token = mock.Mock(return_value='123')
        with mock.patch.object(backend, 'get_token', get_token):
            userinfo = mock.Mock(return_value={
                'is_pku': False
            })
            with mock.patch.object(backend, 'get_userinfo', userinfo):
                user = backend.authenticate(None, '123')
                self.assertEqual(user, None)

    def test_authenticate_with_create_user(self):
        backend = OpenIDClientBackend()
        get_token = mock.Mock(return_value='123')
        userinfo = mock.Mock(
            return_value={
                'is_pku': True,
                'pku_id': '2000000001',
                'name': 'name',
                'email': 'name@pku.edu.cn',
                'website': 'https://www.pku.edu.cn',
                'phone_number': '123456789',
                'is_teacher': True,
                'introduce': 'I am a tester!',
                'department': 'some-department'
            })
        with mock.patch.object(backend, 'get_token', get_token):
            with mock.patch.object(backend, 'get_userinfo', userinfo):
                user = backend.authenticate(None, '123')
                self.assertNotEqual(user, self.user)
                self.assertEqual(user, User.objects.get(pku_id='2000000001'))
                self.assertEqual(user.name, 'name')
                self.assertEqual(user.email, 'name@pku.edu.cn')
                self.assertEqual(user.website, 'https://www.pku.edu.cn')
                self.assertEqual(user.phone_number, '123456789')
                self.assertEqual(user.is_teacher, True)
                self.assertEqual(user.introduce, 'I am a tester!')
                self.assertEqual(user.department, self.department)

    def test_authenticate_with_create_department(self):
        backend = OpenIDClientBackend()
        get_token = mock.Mock(return_value='123')
        userinfo = mock.Mock(
            return_value={
                'is_pku': True,
                'pku_id': '2000000000',
                'department': 'some-department2'
            })
        with mock.patch.object(backend, 'get_token', get_token):
            with mock.patch.object(backend, 'get_userinfo', userinfo):
                user = backend.authenticate(None, '123')
                self.assertEqual(user, self.user)
                self.assertEqual(user.name, '')
                self.assertEqual(user.email, '')
                self.assertEqual(user.website, '')
                self.assertEqual(user.phone_number, '')
                self.assertEqual(user.is_teacher, False)
                self.assertEqual(user.introduce, None)
                self.assertNotEqual(user.department, self.department)
                self.assertEqual(user.department, Department.objects.get(department='some-department2'))


class TestBackend(OpenIDClientBackend):
    def authenticate(self, request, code, **kwargs):
        return User.objects.get(pku_id=code)


class SignalTest(GraphQLTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(pku_id='2000000000')

    @mock.patch('apps.pku_auth.signals.user_create.send')
    def test_user_create_signal_triggered(self, signal):
        backend = OpenIDClientBackend()
        get_token = mock.Mock(return_value='123')
        userinfo = mock.Mock(
            return_value={
                'is_pku': True,
                'pku_id': '2000000001',
                'department': 'some-department2'
            })
        with mock.patch.object(backend, 'get_token', get_token):
            with mock.patch.object(backend, 'get_userinfo', userinfo):
                backend.authenticate(None, '123')
        self.assertTrue(signal.called)
        self.assertEqual(signal.call_count, 1)

    @override_settings(AUTHENTICATION_BACKENDS=['apps.pku_auth.tests.TestBackend'])
    def test_user_logged_in_signal_triggered(self):
        response = self.query(
            '''
            mutation myMutation($input: String!) {
              codeAuth(code: $input) {
                token
                user {
                  lastLogin
                }
                refreshToken
              }
            }
            ''',
            operation_name='myMutation',
            variables={'input': '2000000000'}
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content['data']['codeAuth']['user']['lastLogin'])


class ApiTest(GraphQLTestCase):
    @classmethod
    def setUpTestData(cls):
        OpenIDClient.objects.create(client_id='id1',
                                    client_secret='password1',
                                    authorization_endpoint='http://some.com/1',
                                    token_endpoint='http://some.com/1',
                                    userinfo_endpoint='http://some.com/1',
                                    redirect_uri='http://localhost/1',
                                    scopes='openid profile email')
        OpenIDClient.objects.create(client_id='123',
                                    client_secret='password',
                                    authorization_endpoint='http://some.com/',
                                    token_endpoint='http://some.com/',
                                    userinfo_endpoint='http://some.com/',
                                    redirect_uri='http://localhost/',
                                    scopes='openid profile')
        cls.user = User.objects.create(pku_id='2000000000')

    def test_openid_client(self):
        response = self.query(
            '''
            query{
              openidClient{
                id
                clientId
                authorizationEndpoint
                redirectUri
                scopes
              }
            }
            '''
        )

        content = json.loads(response.content)

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content['data'])
        data = content['data']
        self.assertIsNotNone(data['openidClient'])
        openid_client = data['openidClient']
        self.assertEqual(openid_client['clientId'], '123')
        self.assertEqual(openid_client['authorizationEndpoint'], 'http://some.com/')
        self.assertEqual(openid_client['redirectUri'], 'http://localhost/')
        self.assertEqual(openid_client['scopes'], 'openid profile')

    @override_settings(AUTHENTICATION_BACKENDS=['apps.pku_auth.tests.TestBackend'])
    def test_code_auth(self):
        response = self.query(
            '''
            mutation myMutation($input: String!) {
              codeAuth(code: $input) {
                token
                payload
                user {
                  pkuId
                }
                refreshToken
                refreshExpiresIn
              }
            }
            ''',
            operation_name='myMutation',
            variables={'input': '2000000000'}
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content['data'])
        data = content['data']
        self.assertIsNotNone(data['codeAuth'])
        code_auth = data['codeAuth']
        self.assertEqual(code_auth['payload']['pku_id'], '2000000000')
        self.assertEqual(code_auth['payload'], get_payload(token=code_auth['token']))


class ApiTestWithJWT(GraphQLTestCase):
    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(pku_id='2000000000')

    def test_verify_token(self):
        response = self.query(
            '''
            mutation myMutation($token: String!) {
              verifyToken(token: $token) {
                payload
              }
            }
            ''',
            variables={'token': get_token(self.user)}
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content['data'])
        data = content['data']
        self.assertIsNotNone(data['verifyToken'])
        verify_token = data['verifyToken']
        self.assertIsNotNone(verify_token['payload'])
        payload = verify_token['payload']
        self.assertEqual(payload['pku_id'], self.user.pku_id)

    def test_verify_token_expired(self):
        token = get_token(self.user)
        sleep(1)
        with freeze_time(lambda: datetime.utcnow() + jwt_settings.JWT_EXPIRATION_DELTA):
            response = self.query(
                '''
                mutation myMutation($token: String!) {
                  verifyToken(token: $token) {
                    payload
                  }
                }
                ''',
                variables={'token': token}
            )
            content = json.loads(response.content)
            self.assertResponseHasErrors(response)
            self.assertIsNone(content['data']['verifyToken'])
            self.assertEqual(content['errors'][0]['message'], 'Signature has expired')
