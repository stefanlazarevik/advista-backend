from django.test import TestCase


class ViewsTestCase(TestCase):
    def test_index_loads_properly(self):
        """The index page loads properly"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)


class BaseTest(TestCase):
    def setUp(self):
        self.register_url = '/api/users/'
        self.user = {
            'email': 'test@workspaceit.com',
            'username': 'username',
            'password': 'password',
            'confirm_password': 'password',
            'name': 'fullname'
        }
        self.user_unmatching_password = {
            'email': 'testemail@gmail.com',
            'username': 'username',
            'password': 'teslatt',
            'password2': 'teslatto',
            'name': 'fullname'
        }
        self.user_invalid_email = {
            'email': 'test.com',
            'username': 'username',
            'password': 'teslatt',
            'password2': 'teslatto',
            'name': 'fullname'
        }
        return super().setUp()


class RegisterTest(BaseTest):

    def test_can_register_user(self):
        response = self.client.post(self.register_url, self.user, format='text/html')
        self.assertEqual(response.status_code, 201)

    def test_cant_register_user_with_unmatching_passwords(self):
        response = self.client.post(self.register_url, self.user_unmatching_password, format='text/html')
        self.assertEqual(response.status_code, 400)

    def test_cant_register_user_with_invalid_email(self):
        response = self.client.post(self.register_url, self.user_invalid_email, format='text/html')
        self.assertEqual(response.status_code, 400)

    def test_cant_register_user_with_taken_email(self):
        self.client.post(self.register_url, self.user, format='text/html')
        response = self.client.post(self.register_url, self.user, format='text/html')
        self.assertEqual(response.status_code, 500)