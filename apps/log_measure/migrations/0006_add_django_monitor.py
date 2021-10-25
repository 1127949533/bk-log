# Generated by Django 2.2.6 on 2021-08-21 01:50

from django.db import migrations

from django.conf import settings

from apps.utils.log import logger
from apps.log_measure.constants import DATA_NAMES
from config.domains import MONITOR_APIGATEWAY_ROOT
from bk_monitor.handler.monitor import BKMonitor


def forwards_func(apps, schema_editor):
    try:
        Migration.bk_monitor_client.custom_metric().migrate(data_name_list=Migration.data_names)
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"custom_metric migrate error: {e}")


class Migration(migrations.Migration):
    data_names = DATA_NAMES

    bk_monitor_client = BKMonitor(
        app_id=settings.APP_CODE,
        app_token=settings.SECRET_KEY,
        monitor_host=MONITOR_APIGATEWAY_ROOT,
        report_host=f"{settings.BKMONITOR_CUSTOM_PROXY_IP}/",
        bk_username="admin",
        bk_biz_id=settings.BLUEKING_BK_BIZ_ID,
    )
    dependencies = [
        ("log_measure", "0005_auto_20210821_0950"),
    ]

    operations = [migrations.RunPython(forwards_func)]
