# Generated by Django 4.2.4 on 2023-08-09 16:54

from django.conf import settings
from django.db import migrations, models, transaction
from loguru import logger
from tqdm import tqdm

from takahe.models import Domain as TakaheDomain
from takahe.models import Identity as TakaheIdentity
from takahe.models import User as TakaheUser

domain = settings.SITE_INFO["site_domain"]
service_domain = settings.SITE_INFO.get("site_service_domain")


def init_domain(apps, schema_editor):
    d = TakaheDomain.objects.filter(domain=domain).first()
    if not d:
        logger.info(f"Creating takahe domain {domain}")
        TakaheDomain.objects.create(
            domain=domain,
            local=True,
            service_domain=service_domain,
            notes="NeoDB",
            nodeinfo={},
        )
    else:
        logger.info(f"Takahe domain {domain} already exists")


def init_identity(apps, schema_editor):
    User = apps.get_model("users", "User")
    APIdentity = apps.get_model("users", "APIdentity")
    tdomain = TakaheDomain.objects.filter(domain=domain).first()
    if User.objects.filter(username__isnull=True).exists():
        raise ValueError("null username detected, aborting migration")
    if TakaheUser.objects.exists():
        raise ValueError("existing Takahe users detected, aborting migration")
    if TakaheIdentity.objects.exists():
        raise ValueError("existing Takahe identities detected, aborting migration")
    if APIdentity.objects.exists():
        raise ValueError("existing APIdentity data detected, aborting migration")
    logger.info(f"Creating takahe users/identities")
    for user in tqdm(User.objects.all()):
        username = user.username
        handler = "@" + username
        identity = APIdentity.objects.create(
            pk=user.pk,
            user=user,
            local=True,
            username=username,
            domain_name=domain,
            deleted=None if user.is_active else user.updated,
        )
        takahe_user = TakaheUser.objects.create(pk=user.pk, email=handler)
        takahe_identity = TakaheIdentity.objects.create(
            pk=user.pk,
            actor_uri=f"https://{service_domain or domain}/@{username}@{domain}/",
            profile_uri=user.url,
            username=username,
            domain=tdomain,
            name=username,
            local=True,
            discoverable=not user.preference.no_anonymous_view,
        )
        takahe_identity.generate_keypair()
        takahe_user.identities.add(takahe_identity)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_apidentity"),
    ]

    operations = [
        migrations.RunPython(init_domain),
        migrations.RunPython(init_identity),
    ]