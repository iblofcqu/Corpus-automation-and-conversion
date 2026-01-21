"""
自定义认证模块 - 从HTTP Header读取用户ID
"""

import logging

from django.contrib.auth.models import User
from rest_framework import authentication

logger = logging.getLogger(__name__)


class HeaderAuthentication(authentication.BaseAuthentication):
    """
    从X-User-ID Header读取用户ID并自动创建用户
    用于Nginx auth_request集成
    """

    def authenticate(self, request):
        user_id = request.META.get("HTTP_X_USER_ID")

        if not user_id:
            return None

        # 获取或创建用户
        user, created = User.objects.get_or_create(
            username=user_id,
            defaults={"password": "!"},  # 不可用的密码
        )

        if created:
            # 新用户记录日志
            logger.info("自动创建用户: %s", user_id)

        return (user, None)
