import json

from graphene_django.utils.testing import GraphQLTestCase
from graphql_relay import to_global_id
from graphql_jwt.shortcuts import get_token
from graphql_jwt.settings import jwt_settings
from django.test import TestCase

from apps.pku_auth.signals import user_create

from apps.user.models import User, Department
from apps.user.schema import DepartmentType


class ModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass


class SignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(pku_id="2000000000")
        user_create.send(sender=cls.__class__, user=cls.user)

    def test_signal_callback(self):
        self.assertTrue(self.user.has_perm("change_user", self.user))


class ApiTest(GraphQLTestCase):
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
