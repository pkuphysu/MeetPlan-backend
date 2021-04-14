from django.core.management.base import BaseCommand
from apps.pku_auth.models import OpenIDClient


class Command(BaseCommand):
    help = 'Create an openid client.'

    def handle(self, *args, **options):
        try:
            client_id = input('Please input the client_id: ')
            if client_id == '':
                raise ValueError('client_id can not be empty!')
            client_secret = input('Please input the client_secret: ')
            if client_secret == '':
                raise ValueError('client_secret can not be empty!')
            authorization_endpoint = input('Please input the authorization_endpoint: ')
            if authorization_endpoint == '':
                raise ValueError('authorization_endpoint can not be empty!')
            if not authorization_endpoint.startswith('http'):
                raise ValueError('authorization_endpoint should start with http!')
            token_endpoint = input('Please input the token_endpoint: ')
            if token_endpoint == '':
                raise ValueError('token_endpoint can not be empty!')
            if not token_endpoint.startswith('http'):
                raise ValueError('token_endpoint should start with http!')
            userinfo_endpoint = input('Please input the userinfo_endpoint: ')
            if userinfo_endpoint == '':
                raise ValueError('userinfo_endpoint can not be empty!')
            if not userinfo_endpoint.startswith('http'):
                raise ValueError('userinfo_endpoint should start with http!')
            redirect_uri = input('Please input the redirect_uri: ')
            if redirect_uri == '':
                raise ValueError('redirect_uri can not be empty!')
            if not redirect_uri.startswith('http'):
                raise ValueError('redirect_uri should start with http!')
            scopes = input('Please input the scopes: ')
            if scopes == '':
                raise ValueError('scopes can not be empty!')
            OpenIDClient.objects.create(
                client_id=client_id,
                client_secret=client_secret,
                authorization_endpoint=authorization_endpoint,
                token_endpoint=token_endpoint,
                userinfo_endpoint=userinfo_endpoint,
                redirect_uri=redirect_uri,
                scopes=scopes
            )
            self.stdout.write(self.style.SUCCESS('OpenID client successfully created.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Something goes wrong: {0}'.format(e)))
