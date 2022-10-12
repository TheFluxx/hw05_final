from posts.models import Group, Post, User, Comment
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
import shutil
import tempfile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = User.objects.create_user(
            username='VeryFire'
        )
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertRedirects(response, reverse('posts:user',
                             kwargs={'username':
                                     f'{self.author}'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(Post.objects.first().text, 'text')
        self.assertEqual(PostCreateFormTests.group, self.group)

    def test_guest_create_post(self):
        response = self.guest_client.post(
            reverse('posts:post_create'),
        )
        LOGIN_URL = reverse('users:login')
        POST_CREATE_URL = '/create/'
        self.assertRedirects(response, f'{LOGIN_URL}?next={POST_CREATE_URL}')

    def test_edit_post(self):
        PostCreateFormTests.post = Post.objects.create(
            author=self.author,
            text='text',
        )
        form_data = {
            'text': 'Отредактированный пост',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(Post.objects.first().text, 'Отредактированный пост')
        self.assertEqual(post.author, self.author)

    def test_guest_edit_post(self):
        PostCreateFormTests.post = Post.objects.create(
            author=self.author,
            text='text',
        )
        response = self.guest_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
        )
        LOGIN_URL = reverse('users:login')
        POST_EDIT_URL = f'/posts/{self.post.id}/edit/'
        self.assertRedirects(response, f'{LOGIN_URL}?next={POST_EDIT_URL}')

    def test_guest_comment_post(self):
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'})
        )
        LOGIN_URL = reverse('users:login')
        POST_COMMENT_URL = f'/posts/{self.post.id}/comment/'
        self.assertRedirects(response, f'{LOGIN_URL}?next={POST_COMMENT_URL}')

    def test_authorized_client_add_comment(self):
        """Валидная форма создает запись в Post."""
        PostCreateFormTests.post = Post.objects.create(
            author=self.author,
            text='text',
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'text',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=form_data
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Comment.objects.first().text, 'text')
