# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
License for BK-LOG 蓝鲸日志平台:
--------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
We undertake not to change the open source license (MIT license) applicable to the current version of
the project delivered to anyone in the future.
"""
import time
import logging

import settings
from apps.api import (
    BkItsmApi,
    CCApi,
    JobApi,
    NodeApi,
    BKLoginApi,
    MonitorApi,
    BkDataDatabusApi,
)

from apps.utils.local import activate_request
from apps.utils.thread import generate_request
from apps.exceptions import ApiResultError

from home_application.constants import (
    DEFAULT_SUBSCRIPTION_ID,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_BK_DATA_ID,
)

from iam.api.client import Client

try:
    from blueapps.utils.esbclient import get_client_by_user
except Exception:  # pylint: disable=broad-except
    pass

logger = logging.getLogger()


THIRD_PARTY_CHECK_API = {
    "cc": {"method": CCApi.get_app_list},
    "itsm": {"method": BkItsmApi.get_services},
    "job": {"method": JobApi.get_public_script_list, "kwargs": {"bk_biz_id": settings.BLUEKING_BK_BIZ_ID}},
    "bk_user": {
        "method": BKLoginApi.get_user,
    },
    "nodeman": {
        "method": NodeApi.get_subscription_task_status,
        "kwargs": {"subscription_id": DEFAULT_SUBSCRIPTION_ID},
    },
    "monitor": {
        "method": MonitorApi.search_alarm_strategy_v3,
        "kwargs": {
            "page": DEFAULT_PAGE,
            "page_size": DEFAULT_PAGE_SIZE,
            "bk_biz_id": settings.BLUEKING_BK_BIZ_ID,
        },
    },
    "bk_data": {"method": BkDataDatabusApi.get_cleans, "kwargs": {"raw_data_id": DEFAULT_BK_DATA_ID}},
}


class ThirdParty(object):
    @staticmethod
    def call_api(module: str):
        result = {"status": False, "data": None, "message": ""}
        start_time = time.time()
        try:
            kwargs = THIRD_PARTY_CHECK_API[module].get("kwargs", {})
            _ = THIRD_PARTY_CHECK_API[module]["method"](kwargs)
            result["status"] = True
        except ApiResultError:
            result["status"] = True
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"failed to check {module}, err: {e}")
            result["message"] = str(e)

        spend_time = time.time() - start_time
        result["data"] = "{}ms".format(int(spend_time * 1000))
        return result

    @staticmethod
    def check_paas():
        result = {"status": False, "data": None, "message": ""}
        start_time = time.time()
        if settings.IS_K8S_DEPLOY_MODE:
            activate_request(generate_request())
            from apps.api import BKPAASApi

            try:
                _ = BKPAASApi.get_app_info()
                result["status"] = True
            except ApiResultError:
                result["status"] = True
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"failed to check paas, err: {e}")
                result["message"] = str(e)
        else:
            try:
                client = get_client_by_user(user_or_username=settings.SYSTEM_USE_API_ACCOUNT)
                _ = client.bk_paas.get_app_info()
                result["status"] = True
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"failed to check paas, err: {e}")
                result["message"] = str(e)

        spend_time = time.time() - start_time
        result["data"] = "{}ms".format(int(spend_time * 1000))
        return result

    @staticmethod
    def check_iam():
        result = {"status": False, "data": None, "message": ""}
        app_code = settings.APP_CODE
        app_secret = settings.SECRET_KEY
        bk_iam_host = settings.BK_IAM_INNER_HOST
        bk_paas_host = settings.BK_PAAS_HOST
        start_time = time.time()
        try:
            client = Client(
                app_code=app_code, app_secret=app_secret, bk_iam_host=bk_iam_host, bk_paas_host=bk_paas_host
            )
            status, data = client.ping()
            result["status"] = status
            result["message"] = data.get("message", "")
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"failed to ping iam, err: {e}")
            result["message"] = str(e)
        spend_time = time.time() - start_time
        result["data"] = "{}ms".format(int(spend_time * 1000))

        return result
