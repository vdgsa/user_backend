from .playwright_test_base import PlaywrightTestCase


class LoginPlaywrightTestCase(PlaywrightTestCase):
    def test_ten_test_users_are_available(self) -> None:
        self.assertEqual(len(self.users), 10)

    def test_user_can_sign_in_and_reach_current_user_endpoint(self) -> None:
        user = self.users[0]

        page = self.start_browser()
        page.get(f'{self.live_server_url}/login/?next=/accounts/users/current/')
        page.find_element_by_id('id_username').send_keys(user.username)
        page.find_element_by_id('id_password').send_keys(self.test_password)
        page.find_element_by_css_selector('button[type=submit]').click()

        self.assertIn(user.username, page.find_element_by_css_selector('body').text)
        self.assertEqual(page.current_url, f'{self.live_server_url}/accounts/users/current/')

    def test_invalid_credentials_show_an_error(self) -> None:
        page = self.start_browser()
        page.get(f'{self.live_server_url}/login/')
        page.find_element_by_id('id_username').send_keys('unknown@example.com')
        page.find_element_by_id('id_password').send_keys('incorrect-password')
        page.find_element_by_css_selector('button[type=submit]').click()

        self.assertIn(
            'Please enter a correct Email and password.',
            page.find_element_by_css_selector('body').text
        )
