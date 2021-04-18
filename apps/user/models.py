from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from guardian.mixins import GuardianUserMixin

from apps.user.validators import PKUIDValidator


class Department(models.Model):
    department = models.CharField(_("department"), unique=True, max_length=100)

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self):
        return self.department


class User(AbstractUser, GuardianUserMixin):
    first_name = None
    last_name = None
    username = None
    pku_id_validator = PKUIDValidator()

    pku_id = models.CharField(
        _("pku id"),
        max_length=10,
        unique=True,
        help_text=_("Required. It's your pku id. 10 characters. Digits only."),
        validators=[pku_id_validator],
        error_messages={
            "unique": _("A user with that id already exists."),
        },
    )
    name = models.CharField(_("name"), max_length=40, blank=True)
    email = models.EmailField(_("email address"))
    website = models.URLField(_("website"), max_length=100, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=15, blank=True)
    address = models.CharField(_("address"), max_length=50, blank=True)
    is_teacher = models.BooleanField(
        _("is teacher"),
        default=False,
        help_text=_("Designates whether the user is a teacher."),
    )
    department = models.ForeignKey(
        to=Department,
        on_delete=models.DO_NOTHING,
        verbose_name=_("department"),
        null=True,
        blank=True,
    )
    introduce = models.TextField(
        _("introduce"),
        null=True,
        blank=True,
        help_text=_("Your personal introduction."),
    )
    is_admin = models.BooleanField(
        _("is admin"),
        default=False,
        help_text=_("Admin user can manage this site."),
    )
    REQUIRED_FIELDS = ["email"]
    USERNAME_FIELD = "pku_id"

    class Meta(AbstractUser.Meta):
        abstract = False

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name
