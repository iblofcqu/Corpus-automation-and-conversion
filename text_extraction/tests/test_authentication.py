"""
认证模块测试
"""

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from text_extraction.authentication import HeaderAuthentication


class HeaderAuthenticationTestCase(TestCase):
    """HeaderAuthentication测试用例"""

    def setUp(self):
        self.factory = RequestFactory()
        self.auth = HeaderAuthentication()

    def test_authenticate_with_valid_user_id(self):
        """测试有效的X-User-ID Header"""
        request = self.factory.get("/", HTTP_X_USER_ID="test_user")
        user, auth = self.auth.authenticate(request)

        self.assertIsNotNone(user)
        self.assertIsNone(auth)
        self.assertEqual(user.username, "test_user")
        self.assertTrue(User.objects.filter(username="test_user").exists())

    def test_authenticate_creates_new_user(self):
        """测试自动创建新用户"""
        initial_count = User.objects.count()
        request = self.factory.get("/", HTTP_X_USER_ID="new_user")

        user, _ = self.auth.authenticate(request)

        self.assertEqual(User.objects.count(), initial_count + 1)
        self.assertEqual(user.username, "new_user")

    def test_authenticate_without_header(self):
        """测试没有X-User-ID Header"""
        request = self.factory.get("/")
        result = self.auth.authenticate(request)

        self.assertIsNone(result)

    def test_authenticate_reuses_existing_user(self):
        """测试重用已存在的用户"""
        User.objects.create(username="existing_user")
        initial_count = User.objects.count()

        request = self.factory.get("/", HTTP_X_USER_ID="existing_user")
        user, _ = self.auth.authenticate(request)

        self.assertEqual(User.objects.count(), initial_count)
        self.assertEqual(user.username, "existing_user")
