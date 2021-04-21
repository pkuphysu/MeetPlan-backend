import json
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_token
from graphql_relay import to_global_id
from guardian.shortcuts import assign_perm

from apps.pku_auth.signals import user_create
from apps.user.models import User, Department
from apps.user.schema import DepartmentType, UserType


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


class QueryApiTest(GraphQLTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department1 = Department.objects.create(department="student")
        cls.department2 = Department.objects.create(department="teacher")
        cls.department3 = Department.objects.create(department="admin")
        cls.student = User.objects.create(
            pku_id="2000000000",
            name="student",
            email="student@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="student office",
            department=cls.department1,
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
            department=cls.department2,
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )
        cls.s_admin = User.objects.create(
            pku_id="2000000002",
            name="s_admin",
            email="s_admin@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="s_admin office",
            department=cls.department1,
            introduce="s_admin introduce",
            is_teacher=False,
            is_admin=True,
            is_active=True,
        )
        cls.t_admin = User.objects.create(
            pku_id="2000000003",
            name="t_admin",
            email="t_admin@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="t_admin office",
            department=cls.department3,
            introduce="t_admin introduce",
            is_teacher=True,
            is_admin=True,
            is_active=True,
        )
        cls.users = [cls.student, cls.teacher, cls.s_admin, cls.t_admin]

    @staticmethod
    def get_headers(user):
        return {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {get_token(user)}",
        }

    def test_query_me_without_token(self):
        response = self.query(
            """
            query{
              me{
                id
                pkuId
                lastLogin
                dateJoined
              }
            }
            """
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content["data"])
        data = content["data"]
        self.assertIsNone(data["me"])

    def test_query_me(self):
        for user in self.users:
            department = user.department
            response = self.query(
                """
                query{
                  me{
                    id
                    pkuId
                    name
                    email
                    website
                    department {
                      department
                    }
                    phoneNumber
                    introduce
                    address
                    isActive
                    isTeacher
                    isAdmin
                    lastLogin
                    dateJoined
                  }
                }
                """,
                headers=self.get_headers(user=user),
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertIsNotNone(content["data"])
            data = content["data"]
            self.assertIsNotNone(data["me"])
            me = data["me"]
            self.assertEqual(me["pkuId"], user.pku_id)
            self.assertEqual(me["name"], user.name)
            self.assertEqual(me["email"], user.email)
            self.assertEqual(me["website"], user.website)
            self.assertEqual(me["phoneNumber"], user.phone_number)
            self.assertEqual(me["introduce"], user.introduce)
            self.assertEqual(me["address"], user.address)
            self.assertEqual(me["isActive"], user.is_active)
            self.assertEqual(me["isTeacher"], user.is_teacher)
            self.assertEqual(me["isAdmin"], user.is_admin)
            self.assertIsNone(me["lastLogin"])
            self.assertIsNotNone(me["dateJoined"])
            self.assertIsNotNone(me["department"])
            self.assertEqual(me["department"]["department"], department.department)

    def test_departments_without_token(self):
        response = self.query(
            """
            query{
              departments{
                totalCount
                edges{
                  node{
                    id
                    department
                    userSet {
                      edges {
                        node {
                          id
                        }
                      }
                    }
                  }
                }
              }
            }
            """
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertIsNotNone(content["data"])
        data = content["data"]
        self.assertIsNotNone(data["departments"])
        departments = data["departments"]
        self.assertEqual(departments["totalCount"], 3)
        edges = departments["edges"]
        for edge in edges:
            node = edge["node"]
            self.assertIsNotNone(node)
            self.assertIsNotNone(node["department"])
            self.assertIsNotNone(node["userSet"])
            self.assertEqual(len(node["userSet"]["edges"]), 0)

    def test_departments(self):
        for user in self.users:
            response = self.query(
                """
                query{
                  departments{
                    totalCount
                    edges{
                      node{
                        id
                        department
                        userSet {
                          totalCount
                          edges {
                            node {
                              id
                              name
                              department {
                                department
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertIsNotNone(content["data"])
            data = content["data"]
            self.assertIsNotNone(data["departments"])
            departments = data["departments"]
            self.assertEqual(departments["totalCount"], 3)
            edges = departments["edges"]
            for edge in edges:
                node = edge["node"]
                self.assertIsNotNone(node)
                self.assertIsNotNone(node["department"])
                department = Department.objects.get(department=node["department"])
                self.assertIsNotNone(node["userSet"])
                user_set = node["userSet"]
                self.assertEqual(
                    user_set["totalCount"],
                    len(User.objects.filter(department=department)),
                )
                user_set = user_set["edges"]
                for node2 in user_set:
                    user2 = node2["node"]
                    self.assertEqual(user2["department"]["department"], department.department)

    def test_departments_on_pkuId_field(self):
        # student query user in 'student' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "student"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.student),
        )
        self.assertResponseHasErrors(response)

        # student query user in 'teacher' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "teacher"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.student),
        )
        self.assertResponseHasErrors(response)

        # student query user in 'admin' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "admin"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.student),
        )
        self.assertResponseHasErrors(response)

        # teacher query user in 'student' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "student"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseNoErrors(response)

        # teacher query user in 'teacher' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "teacher"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseNoErrors(response)

        # teacher query user in 'admin' department
        response = self.query(
            """
            query{
              departments(department_Icontains: "admin"){
                edges{
                  node{
                    userSet {
                      edges {
                        node {
                          pkuId
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            headers=self.get_headers(self.teacher),
        )
        self.assertResponseHasErrors(response)

        for user in [self.s_admin, self.t_admin]:
            # teacher query user in 'student' department
            response = self.query(
                """
                query{
                  departments(department_Icontains: "student"){
                    edges{
                      node{
                        userSet {
                          edges {
                            node {
                              pkuId
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            self.assertResponseNoErrors(response)

            # teacher query user in 'teacher' department
            response = self.query(
                """
                query{
                  departments(department_Icontains: "teacher"){
                    edges{
                      node{
                        userSet {
                          edges {
                            node {
                              pkuId
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            self.assertResponseNoErrors(response)

            # teacher query user in 'admin' department
            response = self.query(
                """
                query{
                  departments(department_Icontains: "admin"){
                    edges{
                      node{
                        userSet {
                          edges {
                            node {
                              pkuId
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            self.assertResponseNoErrors(response)

    def test_departments_on_self_limit_field(self):
        for field in ["isActive", "dateJoined", "lastLogin"]:
            # student query user in 'student' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "student"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.student),
            )
            self.assertResponseHasErrors(response)

            # student query user in 'teacher' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "teacher"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.student),
            )
            self.assertResponseHasErrors(response)

            # student query user in 'admin' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "admin"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.student),
            )
            self.assertResponseHasErrors(response)

            # teacher query user in 'student' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "student"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.teacher),
            )
            self.assertResponseHasErrors(response)

            # teacher query user in 'teacher' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "teacher"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.teacher),
            )
            self.assertResponseNoErrors(response)

            # teacher query user in 'admin' department
            response = self.query(
                """
                query{{
                  departments(department_Icontains: "admin"){{
                    edges{{
                      node{{
                        userSet {{
                          edges {{
                            node {{
                              {field}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """.format(
                    field=field
                ),
                headers=self.get_headers(self.teacher),
            )
            self.assertResponseHasErrors(response)

            for user in [self.s_admin, self.t_admin]:
                # teacher query user in 'student' department
                response = self.query(
                    """
                    query{{
                      departments(department_Icontains: "student"){{
                        edges{{
                          node{{
                            userSet {{
                              edges {{
                                node {{
                                  {field}
                                }}
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                    """.format(
                        field=field
                    ),
                    headers=self.get_headers(user),
                )
                self.assertResponseNoErrors(response)

                # teacher query user in 'teacher' department
                response = self.query(
                    """
                    query{{
                      departments(department_Icontains: "teacher"){{
                        edges{{
                          node{{
                            userSet {{
                              edges {{
                                node {{
                                  {field}
                                }}
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                    """.format(
                        field=field
                    ),
                    headers=self.get_headers(user),
                )
                self.assertResponseNoErrors(response)

                # teacher query user in 'admin' department
                response = self.query(
                    """
                    query{{
                      departments(department_Icontains: "admin"){{
                        edges{{
                          node{{
                            userSet {{
                              edges {{
                                node {{
                                  {field}
                                }}
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                    """.format(
                        field=field
                    ),
                    headers=self.get_headers(user),
                )
                self.assertResponseNoErrors(response)

    def test_departments_with_filter_id_exact(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: Float!){
                  departments (id: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["departments"]["totalCount"], count)

        for user in self.users:
            func(user, 1, self.assertResponseNoErrors, 1)
            func(user, 2, self.assertResponseNoErrors, 1)
            func(user, 3, self.assertResponseNoErrors, 1)
            func(user, 4, self.assertResponseNoErrors, 0)
            func(user, 0, self.assertResponseNoErrors, 0)

    def test_departments_with_filter_id_in(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: [String]!){
                  departments (id_In: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["departments"]["totalCount"], count)

        for user in self.users:
            func(user, "1", self.assertResponseNoErrors, 1)
            func(user, "2", self.assertResponseNoErrors, 1)
            func(user, "3", self.assertResponseNoErrors, 1)
            func(user, "4", self.assertResponseNoErrors, 0)
            func(user, "0", self.assertResponseNoErrors, 0)
            func(user, ["0", "1"], self.assertResponseNoErrors, 1)
            func(user, ["1", "2"], self.assertResponseNoErrors, 2)
            func(user, ["1", "2", "3"], self.assertResponseNoErrors, 3)

    def test_departments_with_filter_department_icontains(self):
        def func(user, name, assert_func, count):
            response = self.query(
                """
                query myQuery($name: String!){
                  departments (department_Icontains: $name) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"name": name},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["departments"]["totalCount"], count)

        for user in self.users:
            func(user, "teacher", self.assertResponseNoErrors, 1)
            func(user, "student", self.assertResponseNoErrors, 1)
            func(user, "admin", self.assertResponseNoErrors, 1)
            func(user, "e", self.assertResponseNoErrors, 2)
            func(user, "t", self.assertResponseNoErrors, 2)
            func(user, "n", self.assertResponseNoErrors, 2)

    def test_department_without_token(self):
        for id in range(1, 4):
            response = self.query(
                """
                query myModel($id: ID!){
                  department(id: $id) {
                    id
                    department
                    userSet {
                      edges {
                        node {
                          id
                        }
                      }
                    }
                  }
                }
                """,
                variables={"id": to_global_id(DepartmentType._meta.name, str(id))},
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertIsNotNone(content["data"])
            data = content["data"]
            self.assertIsNotNone(data["department"])
            department = data["department"]
            self.assertIsNotNone(department["id"])
            self.assertIsNotNone(department["department"])
            self.assertIsNotNone(department["userSet"])
            self.assertEqual(len(department["userSet"]["edges"]), 0)

    def test_department(self):
        for id in range(1, 4):
            for user in self.users:
                response = self.query(
                    """
                    query myModel($id: ID!){
                      department(id: $id) {
                        id
                        department
                        userSet {
                          edges {
                            node {
                              id
                            }
                          }
                        }
                      }
                    }
                    """,
                    variables={"id": to_global_id(DepartmentType._meta.name, str(id))},
                    headers=self.get_headers(user),
                )
                content = json.loads(response.content)
                self.assertResponseNoErrors(response)
                self.assertIsNotNone(content["data"])
                data = content["data"]
                self.assertIsNotNone(data["department"])
                department = data["department"]
                self.assertIsNotNone(department["id"])
                self.assertIsNotNone(department["department"])
                self.assertIsNotNone(department["userSet"])
                self.assertEqual(
                    len(department["userSet"]["edges"]),
                    User.objects.filter(department_id=id).count(),
                )

    def test_users_without_token(self):
        for user in self.users:
            response = self.query(
                """
                query {
                  users {
                    totalCount
                    edges {
                      node {
                        id
                        pkuId
                      }
                    }
                  }
                }
                """
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertIsNotNone(content["data"])
            data = content["data"]
            self.assertIsNotNone(data["users"])
            users = data["users"]
            self.assertEqual(users["totalCount"], 0)
            self.assertEqual(users["edges"], [])

    def test_users(self):
        for user in self.users:
            response = self.query(
                """
                query {
                  users {
                    totalCount
                    edges {
                      node {
                        id
                        name
                        email
                        website
                        phoneNumber
                        isTeacher
                        department {
                          department
                        }
                        introduce
                        isAdmin
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            self.assertResponseNoErrors(response)
            self.assertIsNotNone(content["data"])
            data = content["data"]
            self.assertIsNotNone(data["users"])
            users = data["users"]
            self.assertEqual(users["totalCount"], 5)
            edges = users["edges"]
            for edge in edges:
                self.assertIsNotNone(edge["node"])

    def test_users_on_pkuId_field(self):
        for user in self.users:
            response = self.query(
                """
                query {
                  users (isTeacher: false){
                    totalCount
                    edges {
                      node {
                        pkuId
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            if user.is_teacher or user.is_admin:
                self.assertResponseNoErrors(response)
            else:
                self.assertResponseHasErrors(response)
            self.assertEqual(content["data"]["users"]["totalCount"], 3)

            response = self.query(
                """
                query {
                  users (isTeacher: true){
                    totalCount
                    edges {
                      node {
                        pkuId
                      }
                    }
                  }
                }
                """,
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            if user.is_admin:
                self.assertResponseNoErrors(response)
            else:
                self.assertResponseHasErrors(response)
            self.assertEqual(content["data"]["users"]["totalCount"], 2)

    def test_users_on_self_limit_field(self):
        for user in self.users:
            for field in ["isActive", "dateJoined", "lastLogin"]:
                response = self.query(
                    """
                    query {{
                      users {{
                        totalCount
                        edges {{
                          node {{
                            {}
                          }}
                        }}
                      }}
                    }}
                    """.format(
                        field
                    ),
                    headers=self.get_headers(user),
                )
                content = json.loads(response.content)
                if user.is_admin:
                    self.assertResponseNoErrors(response)
                else:
                    self.assertResponseHasErrors(response)
                self.assertEqual(content["data"]["users"]["totalCount"], 5)

    def test_users_with_filter_pkuId_exact(self):
        for user in self.users:
            for pku_id in ["2000000000", "2000000001", "2000000002", "2000000003", "2000000004"]:
                response = self.query(
                    """
                    query myQuery($id: String!){
                      users (pkuId: $id) {
                        totalCount
                        edges {
                          node {
                            id
                          }
                        }
                      }
                    }
                    """,
                    variables={"id": pku_id},
                    headers=self.get_headers(user),
                )
                content = json.loads(response.content)
                self.assertResponseNoErrors(response)
                self.assertEqual(content["data"]["users"]["totalCount"], 0 if pku_id == "2000000004" else 1)

    def test_users_with_filter_pkuId_contains(self):
        def func(user, pku_id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: String!){
                  users (pkuId_Contains: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": pku_id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, "2000000000", self.assertResponseNoErrors, 1)
            func(user, "200000000", self.assertResponseNoErrors, 4)
            func(user, "0", self.assertResponseNoErrors, 5)
            func(user, "1", self.assertResponseNoErrors, 1)
            func(user, "0000000000", self.assertResponseNoErrors, 1)
            func(user, "2", self.assertResponseNoErrors, 4)
            func(user, "3", self.assertResponseNoErrors, 1)

    def test_users_with_filter_pkuId_startswith(self):
        def func(user, pku_id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: String!){
                  users (pkuId_Startswith: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": pku_id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, "2000000000", self.assertResponseNoErrors, 1)
            func(user, "200000000", self.assertResponseNoErrors, 4)
            func(user, "0", self.assertResponseNoErrors, 1)
            func(user, "1", self.assertResponseNoErrors, 0)
            func(user, "0000000000", self.assertResponseNoErrors, 1)
            func(user, "2", self.assertResponseNoErrors, 4)
            func(user, "19", self.assertResponseNoErrors, 0)

    def test_users_with_filter_name_icontains(self):
        def func(user, name, assert_func, count):
            response = self.query(
                """
                query myQuery($name: String!){
                  users (name_Icontains: $name) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"name": name},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, "stu", self.assertResponseNoErrors, 1)
            func(user, "", self.assertResponseNoErrors, 5)
            func(user, "tea", self.assertResponseNoErrors, 1)
            func(user, "admin", self.assertResponseNoErrors, 2)
            func(user, "s", self.assertResponseNoErrors, 2)
            func(user, "t", self.assertResponseNoErrors, 3)
            func(user, "a", self.assertResponseNoErrors, 3)

    def test_users_with_filter_department_id_exact(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: Float!){
                  users (department_Id: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, 1, self.assertResponseNoErrors, 2)
            func(user, 2, self.assertResponseNoErrors, 1)
            func(user, 3, self.assertResponseNoErrors, 1)
            func(user, 4, self.assertResponseNoErrors, 0)
            func(user, 0, self.assertResponseNoErrors, 0)

    def test_users_with_filter_department_id_in(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: [String]!){
                  users (department_Id_In: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, "1", self.assertResponseNoErrors, 2)
            func(user, "2", self.assertResponseNoErrors, 1)
            func(user, "3", self.assertResponseNoErrors, 1)
            func(user, "4", self.assertResponseNoErrors, 0)
            func(user, "0", self.assertResponseNoErrors, 0)
            func(user, ["0", "1"], self.assertResponseNoErrors, 2)
            func(user, ["1", "2"], self.assertResponseNoErrors, 3)
            func(user, ["1", "2", "3"], self.assertResponseNoErrors, 4)

    def test_users_with_filter_department_department_icontains(self):
        def func(user, name, assert_func, count):
            response = self.query(
                """
                query myQuery($name: String!){
                  users (department_Department_Icontains: $name) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"name": name},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, "stu", self.assertResponseNoErrors, 2)
            func(user, "", self.assertResponseNoErrors, 5)
            func(user, "tea", self.assertResponseNoErrors, 1)
            func(user, "admin", self.assertResponseNoErrors, 1)
            func(user, "a", self.assertResponseNoErrors, 2)
            func(user, "s", self.assertResponseNoErrors, 2)
            func(user, "t", self.assertResponseNoErrors, 3)

    def test_users_with_filter_is_teacher_exact(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: Boolean!){
                  users (isTeacher: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, True, self.assertResponseNoErrors, 2)
            func(user, False, self.assertResponseNoErrors, 3)

    def test_users_with_filter_is_admin_exact(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: Boolean!){
                  users (isAdmin: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, True, self.assertResponseNoErrors, 2)
            func(user, False, self.assertResponseNoErrors, 3)

    def test_users_with_filter_is_active_exact(self):
        def func(user, id, assert_func, count):
            response = self.query(
                """
                query myQuery($id: Boolean!){
                  users (isActive: $id) {
                    totalCount
                    edges {
                      node {
                        id
                      }
                    }
                  }
                }
                """,
                variables={"id": id},
                headers=self.get_headers(user),
            )
            content = json.loads(response.content)
            assert_func(response)
            self.assertEqual(content["data"]["users"]["totalCount"], count)

        for user in self.users:
            func(user, True, self.assertResponseNoErrors, 5)
            func(user, False, self.assertResponseNoErrors, 0)


class MutationApiTest(GraphQLTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(department="student")
        cls.user = User.objects.create(
            pku_id="2000000000",
            name="student",
            email="student@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="student office",
            department=cls.department,
            introduce="student introduce",
            is_teacher=False,
            is_admin=False,
            is_active=True,
        )
        cls.user.set_unusable_password()
        cls.user.save()

    @staticmethod
    def get_headers(user):
        return {
            jwt_settings.JWT_AUTH_HEADER_NAME: f"{jwt_settings.JWT_AUTH_HEADER_PREFIX} {get_token(user)}",
        }

    def test_me_without_token(self):
        response = self.query(
            """
            mutation myMutation($input: MeMutationInput!){
              me(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                }
              }
            }
            """,
            input_data={
                "id": to_global_id(UserType._meta.name, str(2)),
                "clientMutationId": "without token",
            },
        )
        self.assertResponseHasErrors(response)

    def test_me(self):
        department = Department.objects.create(department="test")
        response = self.query(
            """
            mutation myMutation($input: MeMutationInput!){
              me(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                  email
                  website
                  phoneNumber
                  address
                  introduce
                  department {
                    department
                  }
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "id": to_global_id(UserType._meta.name, str(self.user.pk)),
                "name": "m student",
                "email": "m.student@pku.edu.cn",
                "website": "https://wwws.pku.edu.cn",
                "phoneNumber": "987654321",
                "address": "m student office",
                "department": to_global_id(DepartmentType._meta.name, str(department.id)),
                "introduce": "m student introduce",
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        me = content["data"]["me"]
        self.assertEqual(me["errors"], [])
        self.assertEqual(me["clientMutationId"], "with token")
        user = me["user"]
        self.assertEqual(user["name"], "m student")
        self.assertEqual(user["email"], "m.student@pku.edu.cn")
        self.assertEqual(user["website"], "https://wwws.pku.edu.cn")
        self.assertEqual(user["phoneNumber"], "987654321")
        self.assertEqual(user["address"], "m student office")
        self.assertEqual(user["department"]["department"], department.department)
        self.assertEqual(user["introduce"], "m student introduce")
        self.user = User.objects.get(id=self.user.id)
        self.assertEqual(self.user.name, "m student"),
        self.assertEqual(self.user.email, "m.student@pku.edu.cn")
        self.assertEqual(self.user.website, "https://wwws.pku.edu.cn")
        self.assertEqual(self.user.phone_number, "987654321")
        self.assertEqual(self.user.address, "m student office")
        self.assertEqual(self.user.department.id, department.id)
        self.assertEqual(self.user.introduce, "m student introduce")

    def test_me_on_no_permission_field(self):
        for item, key in {
            "pkuId": "123",
            "isTeacher": True,
            "isAdmin": True,
            "isActive": True,
            "dateJoined": None,
            "lastLogin": None,
            "password": "123",
        }.items():
            response = self.query(
                """
                mutation myMutation($input: MeMutationInput!){
                  me(input: $input){
                    errors{
                      field
                      message
                    }
                    clientMutationId
                    user{
                      id
                      name
                    }
                  }
                }
                """,
                input_data={
                    "clientMutationId": "with token",
                    "id": to_global_id(UserType._meta.name, str(self.user.pk)),
                    item: key,
                },
                headers=self.get_headers(self.user),
            )
            self.assertResponseHasErrors(response)

    def test_user_create_without_token(self):
        assign_perm("user.add_user", self.user)
        response = self.query(
            """
            mutation myMutation($input: UserCreateInput!){
              userCreate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                }
              }
            }
            """,
            input_data={"clientMutationId": "without token", "email": "test@pku.edu.cn", "pkuId": "2000000001"},
        )
        self.assertResponseHasErrors(response)

    def test_user_create(self):
        self.user.is_admin = True
        self.user.save()
        assign_perm("user.add_user", self.user)
        response = self.query(
            """
            mutation myMutation($input: UserCreateInput!){
              userCreate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  pkuId
                  name
                  website
                  email
                  phoneNumber
                  introduce
                  department {
                    department
                  }
                  isTeacher
                  isAdmin
                  isActive
                  dateJoined
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "pkuId": "2000000001",
                "email": "test@pku.edu.cn",
                "website": "https://phy.pku.edu.cn",
                "phoneNumber": "987654321",
                "introduce": "new user",
                "department": to_global_id(DepartmentType._meta.name, str(self.department.id)),
                "isTeacher": True,
                "isAdmin": False,
                "isActive": True,
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["userCreate"])
        user_create = data["userCreate"]
        self.assertEqual(user_create["errors"], [])
        self.assertEqual(user_create["clientMutationId"], "with token")
        self.assertIsNotNone(user_create["user"])
        user = user_create["user"]
        self.assertEqual(user["pkuId"], "2000000001")
        self.assertEqual(user["email"], "test@pku.edu.cn")
        self.assertEqual(user["website"], "https://phy.pku.edu.cn")
        self.assertEqual(user["phoneNumber"], "987654321")
        self.assertEqual(user["introduce"], "new user")
        self.assertEqual(user["department"]["department"], self.department.department)
        self.assertEqual(user["isTeacher"], True)
        self.assertEqual(user["isAdmin"], False)
        self.assertEqual(user["isActive"], True)
        self.assertIsNotNone(user["dateJoined"])

    def test_user_update_without_token(self):
        assign_perm("user.change_user", self.user)
        user = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="teacher office",
            department=None,
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )
        response = self.query(
            """
            mutation myMutation($input: UserUpdateInput!){
              userUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "without token",
                "id": to_global_id(UserType._meta.name, str(user.id)),
                "email": "test@pku.edu.cn",
                "pkuId": "2000000001",
            },
        )
        self.assertResponseHasErrors(response)

    def test_user_update(self):
        self.user.is_admin = True
        self.user.save()
        assign_perm("user.change_user", self.user)
        user = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="teacher office",
            department=None,
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )
        response = self.query(
            """
            mutation myMutation($input: UserUpdateInput!){
              userUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  pkuId
                  name
                  website
                  email
                  phoneNumber
                  introduce
                  department {
                    department
                  }
                  isTeacher
                  isAdmin
                  isActive
                  dateJoined
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "id": to_global_id(UserType._meta.name, str(user.id)),
                "department": to_global_id(DepartmentType._meta.name, str(self.department.id)),
                "isTeacher": False,
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["userUpdate"])
        user_update = data["userUpdate"]
        self.assertEqual(user_update["errors"], [])
        self.assertEqual(user_update["clientMutationId"], "with token")
        self.assertIsNotNone(user_update["user"])
        user2 = user_update["user"]
        self.assertEqual(user2["department"]["department"], self.department.department)
        self.assertEqual(user2["isTeacher"], False)

    def test_user_delete_without_token(self):
        assign_perm("user.delete_user", self.user)
        user = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="teacher office",
            department=None,
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )
        response = self.query(
            """
            mutation myMutation($input: UserDeleteInput!){
              userDelete(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "without token",
                "id": to_global_id(UserType._meta.name, str(user.id)),
            },
        )
        self.assertResponseHasErrors(response)

    def test_user_delete(self):
        self.user.is_admin = True
        self.user.save()
        assign_perm("user.delete_user", self.user)
        user = User.objects.create(
            pku_id="2000000001",
            name="teacher",
            email="teacher@pku.edu.cn",
            website="https://www.pku.edu.cn",
            phone_number="123456789",
            address="teacher office",
            department=None,
            introduce="teacher introduce",
            is_teacher=True,
            is_admin=False,
            is_active=True,
        )
        response = self.query(
            """
            mutation myMutation($input: UserDeleteInput!){
              userDelete(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  pkuId
                  name
                  website
                  email
                  phoneNumber
                  introduce
                  department {
                    department
                  }
                  isTeacher
                  isAdmin
                  isActive
                  dateJoined
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "id": to_global_id(UserType._meta.name, str(user.id)),
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["userDelete"])
        user_update = data["userDelete"]
        self.assertEqual(user_update["errors"], [])
        self.assertEqual(user_update["clientMutationId"], "with token")
        self.assertIsNotNone(user_update["user"])
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=user.id)

    def test_department_create_without_token(self):
        assign_perm("user.add_department", self.user)
        response = self.query(
            """
            mutation myMutation($input: DepartmentCreateInput!){
              departmentCreate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                user{
                  id
                  name
                }
              }
            }
            """,
            input_data={"clientMutationId": "without token", "department": "teacher"},
        )
        self.assertResponseHasErrors(response)

    def test_department_create(self):
        assign_perm("user.add_department", self.user)
        response = self.query(
            """
            mutation myMutation($input: DepartmentCreateInput!){
              departmentCreate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                department{
                  id
                  department
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "department": "teacher",
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["departmentCreate"])
        department_create = data["departmentCreate"]
        self.assertEqual(department_create["errors"], [])
        self.assertEqual(department_create["clientMutationId"], "with token")
        self.assertIsNotNone(department_create["department"])
        department = department_create["department"]
        self.assertEqual(department["department"], "teacher")

    def test_department_update_without_token(self):
        assign_perm("user.change_department", self.user)
        department = Department.objects.create(department="test")
        response = self.query(
            """
            mutation myMutation($input: DepartmentUpdateInput!){
              departmentUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                department {
                  id
                  department
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "without token",
                "id": to_global_id(DepartmentType._meta.name, str(department.id)),
                "department": "m test",
            },
        )
        self.assertResponseHasErrors(response)

    def test_department_update(self):
        assign_perm("user.change_department", self.user)
        department = Department.objects.create(department="test")
        response = self.query(
            """
            mutation myMutation($input: DepartmentUpdateInput!){
              departmentUpdate(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                department{
                  id
                  department
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "id": to_global_id(DepartmentType._meta.name, str(department.id)),
                "department": "m test",
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["departmentUpdate"])
        department_update = data["departmentUpdate"]
        self.assertEqual(department_update["errors"], [])
        self.assertEqual(department_update["clientMutationId"], "with token")
        self.assertIsNotNone(department_update["department"])
        department2 = department_update["department"]
        department = Department.objects.get(id=department.id)
        self.assertEqual(department2["department"], department.department)

    def test_department_delete_without_token(self):
        assign_perm("user.delete_department", self.user)
        department = Department.objects.create(department="test")
        response = self.query(
            """
            mutation myMutation($input: DepartmentDeleteInput!){
              departmentDelete(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                department{
                  id
                  department
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "without token",
                "id": to_global_id(DepartmentType._meta.name, str(department.id)),
            },
        )
        self.assertResponseHasErrors(response)

    def test_department_delete(self):
        assign_perm("user.delete_department", self.user)
        department = Department.objects.create(department="test")
        response = self.query(
            """
            mutation myMutation($input: DepartmentDeleteInput!){
              departmentDelete(input: $input){
                errors{
                  field
                  message
                }
                clientMutationId
                department {
                  id
                  department
                }
              }
            }
            """,
            input_data={
                "clientMutationId": "with token",
                "id": to_global_id(DepartmentType._meta.name, str(department.id)),
            },
            headers=self.get_headers(self.user),
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        data = content["data"]
        self.assertIsNotNone(data["departmentDelete"])
        department_update = data["departmentDelete"]
        self.assertEqual(department_update["errors"], [])
        self.assertEqual(department_update["clientMutationId"], "with token")
        self.assertIsNotNone(department_update["department"])
        with self.assertRaises(Department.DoesNotExist):
            Department.objects.get(pk=department.id)
