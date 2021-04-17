from django.db import models
from django.utils.translation import gettext_lazy as _


class OpenIDClient(models.Model):
    client_id = models.CharField(_("client id"), max_length=128)
    client_secret = models.CharField(_("client secret"), max_length=128)
    authorization_endpoint = models.URLField(_("authorization endpoint"))
    token_endpoint = models.URLField(_("token endpoint"))
    userinfo_endpoint = models.URLField(_("userinfo endpoint"))
    redirect_uri = models.URLField(_("redirect uri"))
    scopes = models.CharField(_("scopes"), max_length=128)

    class Meta:
        verbose_name = _("OpenID Client")
        verbose_name_plural = _("OpenID Clients")
