from ..models import Post, Group
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class PostCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='test text',
            group=self.group
        )

    def test_index_cache(self):
        """Проверяем, что индексная страница кешируется"""
        first_view = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'changed text'
        post_1.save()
        second_view = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_view.content, second_view.content)
        cache.clear()
        third_view = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_view.content, third_view.content)
