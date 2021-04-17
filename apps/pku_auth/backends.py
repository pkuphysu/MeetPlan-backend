import requests
from django.contrib.auth import get_user_model

from apps.pku_auth.models import OpenIDClient
from apps.pku_auth.signals import user_create
from apps.user.models import Department


class OpenIDClientBackend:
    @staticmethod
    def get_token(client, code):
        res = requests.post(
            client.token_endpoint,
            data={
                "code": code,
                "client_id": client.client_id,
                "client_secret": client.client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": client.redirect_uri,
            },
        )
        token = res.json()
        return token["access_token"]

    @staticmethod
    def get_userinfo(client, token):
        res = requests.get(client.userinfo_endpoint, headers={"Authorization": f"Bearer {token}"})
        return res.json()

    def authenticate(self, request, code, **kwargs):
        client = OpenIDClient.objects.last()
        token = self.get_token(client, code)
        userinfo = self.get_userinfo(client, token)
        if not userinfo["is_pku"]:
            return None

        user, created1 = get_user_model().objects.get_or_create(pku_id=userinfo["pku_id"])
        if created1:
            user.name = userinfo["name"] if "name" in userinfo else ""
            user.email = userinfo["email"] if "email" in userinfo else ""
            user.website = userinfo["website"] if "website" in userinfo else ""
            user.phone_number = userinfo["phone_number"] if "phone_number" in userinfo else ""
            user.address = userinfo["address"]["formatted"] if "address" in userinfo else ""
            user.is_teacher = userinfo["is_teacher"] if "is_teacher" in userinfo else False
            user.introduce = userinfo["introduce"] if "introduce" in userinfo else ""
            user.save(
                update_fields=[
                    "name",
                    "email",
                    "website",
                    "phone_number",
                    "address",
                    "is_teacher",
                    "introduce",
                ]
            )
            user_create.send(sender=self.__class__, user=user)
        if "department" in userinfo:
            department, created2 = Department.objects.get_or_create(department=userinfo["department"])
            if created1:
                user.department = department
                user.save(update_fields=["department"])
            elif created2:
                user.department = department
                user.save(update_fields=["department"])
        return user

    def get_user(self, user_id):
        return None
