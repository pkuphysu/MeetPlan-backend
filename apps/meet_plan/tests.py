import json
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from graphene_django.utils import GraphQLTestCase
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token
from graphql_relay import to_global_id
from guardian.shortcuts import assign_perm

from apps.meet_plan.models import MeetPlan, TermDate, get_start_date
from apps.meet_plan.schema import MeetPlanType
from apps.user.models import User
from apps.user.schema import UserType


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

    def test_manager(self):
        now = timezone.now()
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now - timedelta(days=366))
        self.assertEqual(MeetPlan.objects.count(), 1)
        self.assertEqual(MeetPlan.objects.get_queryset(start_date=get_start_date()).count(), 0)

        TermDate.objects.create(start_date=timezone.now())

        self.assertEqual(MeetPlan.objects.count(), 1)
        self.assertEqual(MeetPlan.objects.get_queryset(start_date=get_start_date()).count(), 0)
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now)
        self.assertEqual(MeetPlan.objects.count(), 2)
        self.assertEqual(MeetPlan.objects.get_queryset(start_date=get_start_date()).count(), 0)
        MeetPlan.objects.create(teacher=self.teacher, place=self.teacher.address, start_time=now + timedelta(seconds=1))
        self.assertEqual(MeetPlan.objects.count(), 3)
        self.assertEqual(MeetPlan.objects.get_queryset(start_date=get_start_date()).count(), 1)
        self.assertEqual(MeetPlan.objects.get_queryset(start_date=now - timedelta(days=366)).count(), 2)

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


class QueryApiTest(GraphQLTestCase):
    @staticmethod
    def get_headers(user):
        return {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {get_token(user)}",
        }

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create(pku_id="1999999999", name="admin", email="admin@pku.edu.cn", is_admin=True)
        cls.student = User.objects.create(
            pku_id="2000000000",
            name="student",
            email="student@pku.edu.cn",
        )
        cls.student2 = User.objects.create(
            pku_id="2000000001",
            name="student2",
            email="student2@pku.edu.cn",
        )
        cls.teacher1 = User.objects.create(
            pku_id="2000000002",
            name="teacher",
            email="teacher@pku.edu.cn",
            address="teacher office",
            is_teacher=True,
        )
        cls.teacher2 = User.objects.create(
            pku_id="2000000003",
            name="teacher2",
            email="teacher2@pku.edu.cn",
            address="teacher2 office",
            is_teacher=True,
        )
        TermDate.objects.create(start_date=timezone.now())
        MeetPlan.objects.create(
            teacher=cls.teacher1,
            place=cls.teacher1.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
            student=cls.student,
            complete=False,
        )
        MeetPlan.objects.create(
            teacher=cls.teacher2,
            place=cls.teacher2.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
            student=cls.student2,
            complete=True,
        )
        MeetPlan.objects.create(
            teacher=cls.teacher1,
            place=cls.teacher1.address,
            start_time=timezone.now() - timedelta(hours=1),
            duration=2,
        )
        MeetPlan.objects.create(
            teacher=cls.teacher2,
            place=cls.teacher2.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=3,
        )

    def test_term_date_without_token(self):
        response = self.query(
            """
            query{
              termDate{
                startDate
              }
            }
            """
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["termDate"]["startDate"], get_start_date().isoformat())

    def test_meet_plans_without_token(self):
        response = self.query(
            """
            {
              meetPlans {
                totalCount
                edges {
                  node {
                    id
                    pk
                    teacher {
                      id
                      name
                    }
                    place
                    startTime
                    duration
                    tMessage
                    available
                  }
                }
              }
            }
            """
        )
        content = json.loads(response.content)
        self.assertResponseHasErrors(response)
        self.assertIsNone(content["data"]["meetPlans"])

    def test_meet_plans_stu(self):
        response = self.query(
            """
            {
              meetPlans {
                totalCount
                edges {
                  node {
                    id
                    pk
                    teacher {
                      id
                      name
                    }
                    place
                    startTime
                    duration
                    tMessage
                    available
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlans"]["totalCount"], 4)
        self.assertFalse(content["data"]["meetPlans"]["edges"][0]["node"]["available"])
        self.assertFalse(content["data"]["meetPlans"]["edges"][1]["node"]["available"])
        self.assertFalse(content["data"]["meetPlans"]["edges"][2]["node"]["available"])
        self.assertTrue(content["data"]["meetPlans"]["edges"][3]["node"]["available"])

        response = self.query(
            """
            {
              meetPlans {
                totalCount
                edges {
                  node {
                    id
                    pk
                    teacher {
                      id
                      name
                    }
                    place
                    startTime
                    duration
                    tMessage
                    available
                    student {
                      id
                      name
                    }
                    sMessage
                    complete
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseHasErrors(response)
        self.assertEqual(len(content["errors"]), 9)
        self.assertIsNotNone(content["data"]["meetPlans"]["edges"][0]["node"]["student"])
        self.assertIsNone(content["data"]["meetPlans"]["edges"][1]["node"]["student"])
        self.assertIsNone(content["data"]["meetPlans"]["edges"][2]["node"]["student"])
        self.assertIsNone(content["data"]["meetPlans"]["edges"][3]["node"]["student"])

    def test_meet_plans_tea(self):
        query_stat = """
        {
          meetPlans {
            totalCount
            edges {
              node {
                id
                pk
                teacher {
                  id
                  name
                }
                place
                startTime
                duration
                tMessage
                available
                student {
                  id
                  pkuId
                  name
                }
                sMessage
                complete
              }
            }
          }
        }
        """
        response = self.query(query_stat, headers=self.get_headers(self.teacher1))
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlans"]["totalCount"], 2)
        self.assertFalse(content["data"]["meetPlans"]["edges"][0]["node"]["available"])
        self.assertFalse(content["data"]["meetPlans"]["edges"][1]["node"]["available"])

        response = self.query(query_stat, headers=self.get_headers(self.teacher2))
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlans"]["totalCount"], 2)
        self.assertFalse(content["data"]["meetPlans"]["edges"][0]["node"]["available"])
        self.assertTrue(content["data"]["meetPlans"]["edges"][1]["node"]["available"])

    def test_meet_plans_admin(self):
        query_stat = """
        {
          meetPlans {
            totalCount
            edges {
              node {
                id
                pk
                teacher {
                  id
                  name
                }
                place
                startTime
                duration
                tMessage
                available
                student {
                  id
                  pkuId
                  name
                  dateJoined
                }
                sMessage
                complete
              }
            }
          }
        }
        """
        response = self.query(query_stat, headers=self.get_headers(self.admin))
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlans"]["totalCount"], 4)
        self.assertFalse(content["data"]["meetPlans"]["edges"][0]["node"]["available"])
        self.assertFalse(content["data"]["meetPlans"]["edges"][1]["node"]["available"])
        self.assertFalse(content["data"]["meetPlans"]["edges"][2]["node"]["available"])
        self.assertTrue(content["data"]["meetPlans"]["edges"][3]["node"]["available"])

    def test_meet_plans_filter_teacher_id_exact(self):
        for i in range(2, 7):
            response = self.query(
                """
                query myQuery($id: Float!){
                  meetPlans(teacher_Id: $id) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"id": i},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(teacher_id=i).count())

    def test_meet_plans_filter_teacher_id_in(self):
        def test(id, count):
            response = self.query(
                """
                query myQuery($id: [String]){
                  meetPlans(teacher_Id_In: $id) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"id": id},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(content["data"]["meetPlans"]["totalCount"], count)

        test(["2"], MeetPlan.objects.filter(teacher_id__in=[2]).count())
        test(["3"], MeetPlan.objects.filter(teacher_id__in=[3]).count())
        test(["4"], MeetPlan.objects.filter(teacher_id__in=[4]).count())
        test(["5"], MeetPlan.objects.filter(teacher_id__in=[5]).count())
        test(["6"], MeetPlan.objects.filter(teacher_id__in=[6]).count())
        test(["2", "3"], MeetPlan.objects.filter(teacher_id__in=[2, 3]).count())
        test(["2", "5"], MeetPlan.objects.filter(teacher_id__in=[2, 5]).count())
        test(["6", "5"], MeetPlan.objects.filter(teacher_id__in=[6, 5]).count())

    def test_meet_plans_filter_start_time_lt(self):
        def test(time):
            response = self.query(
                """
                query myQuery($time: DateTime!){
                  meetPlans(startTime_Lt: $time) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"time": time.isoformat()},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(start_time__lt=time).count()
            )

        test(timezone.now())
        test(timezone.now() - timedelta(hours=2))
        test(get_start_date())

    def test_meet_plans_filter_start_time_gt(self):
        def test(time):
            response = self.query(
                """
                query myQuery($time: DateTime!){
                  meetPlans(startTime_Gt: $time) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"time": time.isoformat()},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(start_time__gt=time).count()
            )

        test(timezone.now())
        test(timezone.now() - timedelta(minutes=10))
        test(timezone.now() - timedelta(hours=2))
        test(get_start_date())

    def test_meet_plans_filter_duration_exact(self):
        def test(duration):
            response = self.query(
                """
                query myQuery($duration: String!){
                  meetPlans(duration: $duration) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"duration": str(duration)},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(duration__exact=duration).count()
            )

        test(1)
        test(2)
        test(3)
        test(4)

    def test_meet_plans_filter_duration_in(self):
        def test(duration):
            response = self.query(
                """
                query myQuery($duration: [String]){
                  meetPlans(duration_In: $duration) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(self.student),
                variables={"duration": duration},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(duration__in=duration).count()
            )

        test(["1"])
        test(["2"])
        test(["3"])
        test(["1", "4"])
        test(["1", "3"])
        test(["2", "3"])
        test(["3", "4"])

    def test_meet_plans_filter_student_pku_id_exact(self):
        def test(pku_id, user):
            response = self.query(
                """
                query myQuery($student_PkuId: String!){
                  meetPlans(student_PkuId: $student_PkuId) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                        student {
                          id
                          pkuId
                          name
                          dateJoined
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
                variables={"student_PkuId": pku_id},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"],
                MeetPlan.objects.filter(student__pku_id__exact=pku_id).count(),
            )

        # TODO: when make this filter only for admin, uncomment next line
        # test(self.student.pku_id, self.student)
        # test(self.student2.pku_id, self.student2)
        # test(self.student2.pku_id, self.student)
        test(self.student.pku_id, self.admin)
        test(self.student2.pku_id, self.admin)

    def test_meet_plans_filter_student_pku_id_contains(self):
        def test(pku_id, user):
            response = self.query(
                """
                query myQuery($student_PkuId: String!){
                  meetPlans(student_PkuId_Contains: $student_PkuId) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                        student {
                          id
                          pkuId
                          name
                          dateJoined
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
                variables={"student_PkuId": pku_id},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"],
                MeetPlan.objects.filter(student__pku_id__contains=pku_id).count(),
            )

        # TODO: when make this filter only for admin, uncomment next and fix them
        # test("123123", self.student)
        # test("123123", self.student2)
        # test(self.student2.pku_id, self.student)
        test("123123", self.admin)
        test("20", self.admin)
        test("000000000", self.admin)
        test("000000001", self.admin)

    def test_meet_plans_filter_student_pku_id_startswith(self):
        def test(pku_id, user):
            response = self.query(
                """
                query myQuery($student_PkuId: String!){
                  meetPlans(student_PkuId_Contains: $student_PkuId) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                        student {
                          id
                          pkuId
                          name
                          dateJoined
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
                variables={"student_PkuId": pku_id},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"],
                MeetPlan.objects.filter(student__pku_id__startswith=pku_id).count(),
            )

        # TODO: when make this filter only for admin, uncomment next and fix them
        # test("123123", self.student)
        # test("123123", self.student2)
        # test(self.student2.pku_id, self.student)
        test("123123", self.admin)
        test("20", self.admin)
        test("19", self.admin)
        test("2000000000", self.admin)

    def test_meet_plans_filter_complete_exact(self):
        def test(complete, user):
            response = self.query(
                """
                query myQuery($complete: Boolean!){
                  meetPlans(complete: $complete) {
                    totalCount
                    edges {
                      node {
                        id
                        pk
                        teacher {
                          id
                          name
                        }
                        place
                        startTime
                        duration
                        tMessage
                        available
                        student {
                          id
                          pkuId
                          name
                          dateJoined
                        }
                        complete
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
                variables={"complete": complete},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertEqual(
                content["data"]["meetPlans"]["totalCount"], MeetPlan.objects.filter(complete__exact=complete).count()
            )

        test(True, self.admin)
        test(False, self.admin)


class MutationApiTest(GraphQLTestCase):
    @staticmethod
    def get_headers(user):
        return {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {get_token(user)}",
        }

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create(pku_id="1999999999", name="admin", email="admin@pku.edu.cn", is_admin=True)
        assign_perm("meet_plan.add_termdate", cls.admin)
        cls.student = User.objects.create(
            pku_id="2000000000",
            name="student",
            email="student@pku.edu.cn",
        )
        cls.teacher = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            address="teacher office",
            is_teacher=True,
        )
        TermDate.objects.create(start_date=timezone.now())

    def test_term_date_update(self):
        response = self.query(
            """
            query{
              termDate{
                startDate
              }
            }
            """
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["termDate"]["startDate"], TermDate.objects.last().start_date.isoformat())
        now = timezone.now()
        response = self.query(
            """
            mutation myMutation($input: TermDateCreateInput!){
              termDateUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                termDate {
                  id
                  startDate
                }
              }
            }
            """,
            input_data={"clientMutationId": "without token", "startDate": now.isoformat()},
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertGreater(len(content["data"]["termDateUpdate"]["errors"]), 0)

        response = self.query(
            """
            mutation myMutation($input: TermDateCreateInput!){
              termDateUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                termDate {
                  id
                  startDate
                }
              }
            }
            """,
            headers=self.get_headers(self.admin),
            input_data={"clientMutationId": "with token", "startDate": now.isoformat()},
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["termDateUpdate"]["termDate"]["startDate"], now.isoformat())

    def test_meet_plan_create_admin(self):
        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
            },
            headers=self.get_headers(self.admin),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        mt = MeetPlan.objects.get(pk=content["data"]["meetPlanCreate"]["meetPlan"]["pk"])
        self.assertTrue(self.teacher.has_perms(["meet_plan.change_meetplan", "meet_plan.delete_meetplan"], mt))

    def test_meet_plan_create_teacher(self):
        teacher = User.objects.create(
            pku_id="2000000002",
            name="teacher2",
            email="teacher2@pku.edu.cn",
            address="teacher2 office",
            is_teacher=True,
        )
        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
            },
            headers=self.get_headers(self.teacher),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        mt = MeetPlan.objects.get(pk=content["data"]["meetPlanCreate"]["meetPlan"]["pk"])
        self.assertTrue(self.teacher.has_perms(["meet_plan.change_meetplan", "meet_plan.delete_meetplan"], mt))

        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
            },
            headers=self.get_headers(teacher),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanCreate"]["errors"], [])

    def test_meet_plan_create_student(self):
        student = User.objects.create(
            pku_id="2000000002",
            name="student2",
            email="student2@pku.edu.cn",
        )
        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanCreate"]["errors"], [])

        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
                "student": to_global_id(UserType._meta.name, str(student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanCreate"]["errors"], [])

        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": (timezone.now() + timedelta(minutes=1)).isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanCreate"]["errors"], [])

        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
                "complete": True,
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanCreate"]["errors"], [])

        response = self.query(
            """
            mutation myMutation($input: MeetPlanCreateInput!){
              meetPlanCreate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "teacher": to_global_id(UserType._meta.name, str(self.teacher.id)),
                "place": self.teacher.address,
                "startTime": timezone.now().isoformat(),
                "duration": 1,
                "tMessage": "test meet plan",
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanCreate"]["errors"], [])
        mt = MeetPlan.objects.get(pk=content["data"]["meetPlanCreate"]["meetPlan"]["pk"])
        self.assertTrue(self.teacher.has_perms(["meet_plan.change_meetplan", "meet_plan.delete_meetplan"], mt))

    def test_meet_plan_update_admin(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now(),
            duration=1,
        )
        response = self.query(
            """
            mutation myMutation($input: MeetPlanUpdateInput!){
              meetPlanUpdate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "startTime": timezone.now().isoformat(),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.admin),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanUpdate"]["errors"], [])

    def test_meet_plan_update_teacher(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now(),
            duration=1,
        )
        assign_perm("meet_plan.change_meetplan", self.teacher, mt)
        teacher = User.objects.create(
            pku_id="2000000002",
            name="teacher2",
            email="teacher2@pku.edu.cn",
            address="teacher2 office",
            is_teacher=True,
        )

        query_str = """
            mutation myMutation($input: MeetPlanUpdateInput!){
              meetPlanUpdate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "startTime": timezone.now().isoformat(),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
                "complete": True,
            },
            headers=self.get_headers(self.teacher),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "teacher": to_global_id(UserType._meta.name, str(teacher.id)),
                "startTime": timezone.now().isoformat(),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
                "complete": True,
            },
            headers=self.get_headers(self.teacher),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "startTime": timezone.now().isoformat(),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
                "complete": True,
            },
            headers=self.get_headers(teacher),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

    def test_meet_plan_update_student(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
        )
        student = User.objects.create(
            pku_id="2000000002",
            name="student2",
            email="student2@pku.edu.cn",
        )

        query_str = """
            mutation myMutation($input: MeetPlanUpdateInput!){
              meetPlanUpdate(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """

        # 安排未被选取时的测试逻辑
        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "teacher": to_global_id(UserType._meta.name, str(student.id)),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "startTime": timezone.now().isoformat(),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "place": self.student.address,
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "duration": 2,
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "tMessage": "test hhhh",
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        mt.start_time = timezone.now()
        mt.save()

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        mt.start_time = timezone.now() + timedelta(hours=1)
        mt.student = self.student
        mt.save()

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": to_global_id(UserType._meta.name, str(student.id)),
                "sMessage": "test hhh",
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": None,
                "sMessage": "test hhh",
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id)), "sMessage": "test hhh"},
            headers=self.get_headers(student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id)), "complete": True},
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertNotEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        mt.student = None
        mt.save()

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanUpdate"]["errors"], [])

        response = self.query(
            query_str,
            input_data={
                "id": to_global_id(MeetPlanType._meta.name, str(mt.id)),
                "student": to_global_id(UserType._meta.name, str(self.student.id)),
                "sMessage": "test",
            },
            headers=self.get_headers(self.student),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanUpdate"]["errors"], [])

    def test_meet_plan_delete_admin(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
            student=self.student,
            complete=True,
        )

        query_str = """
            mutation myMutation($input: MeetPlanDeleteInput!){
              meetPlanDelete(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.admin),
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertGreater(len(content["data"]["meetPlanDelete"]["errors"]), 0)
        self.assertEqual(MeetPlan.objects.all().count(), 1)

        mt.student = None
        mt.save()

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.admin),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["meetPlanDelete"]["errors"], [])
        self.assertEqual(MeetPlan.objects.all().count(), 0)

    def test_meet_plan_delete_teacher(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
            student=self.student,
            complete=True,
        )

        query_str = """
            mutation myMutation($input: MeetPlanDeleteInput!){
              meetPlanDelete(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertGreater(len(content["data"]["meetPlanDelete"]["errors"]), 0)
        self.assertEqual(MeetPlan.objects.all().count(), 1)

        mt.student = None
        mt.save()

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertGreater(len(content["data"]["meetPlanDelete"]["errors"]), 0)
        self.assertEqual(MeetPlan.objects.all().count(), 1)

        assign_perm("meet_plan.delete_meetplan", self.teacher, mt)

        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseNoErrors(response)
        self.assertEqual(MeetPlan.objects.all().count(), 0)

    def test_meet_plan_delete_student(self):
        mt = MeetPlan.objects.create(
            teacher=self.teacher,
            place=self.teacher.address,
            start_time=timezone.now() + timedelta(hours=1),
            duration=1,
            student=self.student,
            complete=True,
        )

        query_str = """
            mutation myMutation($input: MeetPlanDeleteInput!){
              meetPlanDelete(input: $input){
                errors {
                  field
                  message
                }
                clientMutationId
                meetPlan{
                  id
                  pk
                  teacher {
                    id
                    name
                  }
                  place
                  startTime
                  duration
                  tMessage
                  available
                  student {
                    id
                    name
                  }
                  sMessage
                  complete
                }
              }
            }
            """
        response = self.query(
            query_str,
            input_data={"id": to_global_id(MeetPlanType._meta.name, str(mt.id))},
            headers=self.get_headers(self.student),
        )
        self.assertResponseNoErrors(response)
        content = json.loads(response.content)
        self.assertGreater(len(content["data"]["meetPlanDelete"]["errors"]), 0)
        self.assertEqual(MeetPlan.objects.all().count(), 1)
