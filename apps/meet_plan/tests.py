from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from apps.meet_plan.models import MeetPlan
from apps.user.models import User


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

    def test_queryset(self):
        now = timezone.now()
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now)
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now + timedelta(minutes=1))
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now, student=self.student)
        mp4 = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=now + timedelta(minutes=1),
            student=self.student,
        )
        self.assertEqual(MeetPlan.objects.available().filter(available=True).count(), 1)
        mp4.student = None
        mp4.save()
        self.assertEqual(MeetPlan.objects.available().filter(available=True).count(), 2)
        with freeze_time(lambda: now + timedelta(minutes=1)):
            self.assertEqual(MeetPlan.objects.available().filter(available=True).count(), 0)

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
