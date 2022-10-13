from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Post, Group, User
from django.urls import reverse
from django.core.cache import cache


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_page_accessibility(self):
        url_names = ('/', f'/group/{self.group.slug}/',
                     f'/posts/{self.post.id}/')
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_urls_httpstatus(self):
        response = self.author_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            ('posts/group_list.html', f'/group/{self.group.slug}/'),
            ('posts/post_detail.html', f'/posts/{self.post.id}/'),
        )
        for template, address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def accessibility_of_the_edit_page(self):
        response = self.author_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisting_page_url_exists_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_author_url_uses_correct_template(self):
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_guest_redirect(self):
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        LOGIN_URL = reverse('users:login')
        POST_EDIT_URL = f'/posts/{self.post.id}/edit/'
        self.assertRedirects(response, f'{LOGIN_URL}?next={POST_EDIT_URL}')

    def test_no_author_redirect(self):
        no_author = User.objects.create_user(username='no_author')
        no_author_client = Client()
        no_author_client.force_login(no_author)

        response = no_author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id':
                                     f'{self.post.id}'}))

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
