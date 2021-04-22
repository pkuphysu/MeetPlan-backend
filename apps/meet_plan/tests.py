from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.meet_plan.models import MeetPlan
from apps.user.models import User


class AdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.teacher = cls.admin = User.objects.create(
            pku_id="2000000000",
            name="admin",
            address="admin office",
            is_teacher=True,
            is_admin=True,
            is_superuser=True,
        )
        cls.student = User.objects.create(
            pku_id="2000000001",
            name="student",
            email="student@pku.edu.cn",
        )
        now = timezone.now()
        MeetPlan.objects.create(teacher=cls.teacher, place=cls.teacher.address, start_time=now, duration=1)
        MeetPlan.objects.create(
            teacher=cls.teacher, place=cls.teacher.address, start_time=now + timedelta(minutes=1), duration=1
        )
        MeetPlan.objects.create(
            teacher=cls.teacher,
            place=cls.teacher.address,
            start_time=now + timedelta(hours=1),
            duration=1,
            student=cls.student,
        )

    def test_admin_page(self):
        self.client.force_login(self.admin, backend="django.contrib.auth.backends.ModelBackend")
        response = self.client.get(path=reverse("admin:meet_plan_meetplan_changelist"))
        self.assertEqual(response.status_code, 200)
        self.client.get(path=reverse("admin:meet_plan_meetplan_changelist"), data={"available": "yes"})
        self.assertEqual(response.status_code, 200)
        self.client.get(path=reverse("admin:meet_plan_meetplan_changelist"), data={"available": "no"})
        self.assertEqual(response.status_code, 200)


class ModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create(
            pku_id="2000000000",
            name="student",
            email="student@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="student office",
            introduce="student introduce",
            is_teacher=False,
            is_admin=False,
            is_active=True,
        )
        cls.teacher = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="teacher office",
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )

    def test_available(self):
        meet_plan = MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=timezone.now())
        self.assertFalse(meet_plan.is_available())
        meet_plan.start_time = timezone.now() + timedelta(minutes=1)
        meet_plan.save()
        self.assertTrue(meet_plan.is_available())
        meet_plan.student = self.student
        self.assertFalse(meet_plan.is_available())

    def test_save(self):
        now = timezone.now()
        mp = MeetPlan.objects.create(
            teacher=self.teacher, place=self.teacher.address, start_time=now + timedelta(minutes=1)
        )
        self.assertIsNone(mp.student)
        mp.student = self.student
        mp.s_message = "test"
        mp.complete = True
        mp.save()
        self.assertEqual(mp.s_message, "test")
        self.assertTrue(mp.complete)
        mp.student = None
        mp.save()
        self.assertEqual(mp.s_message, "")
        self.assertFalse(mp.complete)
        self.assertTrue(mp.is_available())
        with freeze_time(lambda: now + timedelta(minutes=1)):
            self.assertFalse(mp.is_available())
