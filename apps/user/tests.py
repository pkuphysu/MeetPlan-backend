from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from apps.pku_auth.signals import user_create
from apps.user.models import User, Department


class ModelTest(TestCase):
    def test_department(self):
        department = Department.objects.create(department="123")
        self.assertEqual(department.__str__(), "123")

    def test_user(self):
        user = User.objects.create(name="alice")
        self.assertEqual(user.get_full_name(), "alice")
        self.assertEqual(user.get_short_name(), "alice")


class CommandTest(TestCase):
    @mock.patch("apps.pku_auth.management.commands.createclient.input")
    def _call_wrapper(self, response_value, mock_input=None):
        def input_response(message):
            return response_value

        mock_input.side_effect = input_response
        out = StringIO()
        call_command("createclient", stdout=out)
        return out.getvalue().rstrip()

    def test_command(self):
        self.assertIn("OpenID client successfully created.", self._call_wrapper("http"))


class SignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(pku_id="2000000000")
        user_create.send(sender=cls.__class__, user=cls.user)

    def test_signal_callback(self):
        self.assertTrue(self.user.has_perm("change_user", self.user))
