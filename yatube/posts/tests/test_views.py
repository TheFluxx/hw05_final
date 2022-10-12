from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from http import HTTPStatus
from posts.forms import PostForm
from yatube.settings import NUM_POSTS, SMALL_GIF
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from posts.models import Post, Group, User, Follow


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём авторизованного пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        # Создаём группу в бд
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Создаём запись в бд
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        cache.clear()
        PostViewsTest.authorized_client = Client()
        PostViewsTest.authorized_client.force_login(self.user)

    def post_exist(self, page_context):
        """Метод для проверки существования поста на страницах."""
        if 'page_obj' in page_context:
            post = page_context['page_obj'][0]
        else:
            post = page_context['post']
        task_author = post.author
        task_text = post.text
        task_group = post.group
        self.assertEqual(
            task_author,
            self.post.author
        )
        self.assertEqual(
            task_text,
            self.post.text
        )
        self.assertEqual(
            task_group,
            self.post.group
        )

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            (reverse('posts:group_list', kwargs={
                'slug': PostViewsTest.group.slug})):
                    'posts/group_list.html',

            (reverse('posts:user', kwargs={
                'username': 'StasBasov'})): 'posts/profile.html',

            (reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})): 'posts/post_detail.html',

            (reverse('posts:post_edit', kwargs={
                'post_id': self.post.id})): 'posts/create_post.html',

            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name вызывается соответствующий шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_page_show_correct_context(self):
        """Проверка контекста index."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        self.assertEqual(post_object.text, PostViewsTest.post.text)
        self.assertEqual(post_object.group.title, PostViewsTest.group.title)
        self.assertEqual(post_object.image, PostViewsTest.post.image)

    def test_group_list_show_correct_context(self):
        """Проверка контекста group_list."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PostViewsTest.group.slug}'}
            )
        )
        self.assertIn('page_obj', response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(PostViewsTest.user, post.author)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(PostViewsTest.group, post.group)
        self.assertEqual(post.image, PostViewsTest.post.image)

    def test_profile_show_correct_context(self):
        """Проверка контекста profile"""
        response = self.authorized_client.get(
            reverse(
                'posts:user',
                kwargs={'username': 'StasBasov'}
            )
        )
        post_object = response.context['page_obj'].object_list[0]
        self.assertEqual(post_object.text, 'Тестовый текст')
        self.assertEqual(PostViewsTest.group, post_object.group)
        self.assertEqual(PostViewsTest.user, post_object.author)
        self.assertEqual(post_object.image, PostViewsTest.post.image)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста post_detail."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        post_object = response.context['post']
        self.assertEqual(self.post, post_object)
        self.assertEqual(post_object.image, PostViewsTest.post.image)

    def test_post_edit_show_correct_context(self):
        """Проверка контекста post_edit."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertIsInstance(response.context.get('is_edit'), bool)

    def test_create_post_show_correct_context(self):
        """Проверка контекста create_post."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_new_post_exists(self):
        """Новый пост появляется на страницах index, group_list,
        profile, если при его создании указать группу.
        """
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:user', kwargs={'username': 'StasBasov'}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post.text, 'Тестовый текст')
                self.assertEqual(PostViewsTest.user, post.author)
                self.assertEqual(PostViewsTest.group, post.group)

    def test_new_post_absence(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse('posts:index'))
        PostViewsTest.group_two = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-two',
            description='Тестовое описание 2',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост1',
            group=self.group_two
        )
        self.assertNotEqual(response.context.get('page_obj')[0].group,
                            self.group_two)

    def test_follow(self):
        """Тестирование подписки на автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Тестирование отписки от автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Lermontov')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        response_follow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_follow = response_follow.context
        self.post_exist(context_follow)

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        new_user = User.objects.create(username='Lermontov')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        response_unfollow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUp(self):
        cache.clear()
        super().setUpClass()
        self.user = User.objects.create_user(username='StasBasov')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = []
        for i in range(13):
            posts.append(
                Post(text=f'Тестовый текст {i}',
                     group=self.group, author=self.user)
            )
        Post.objects.bulk_create(posts)

    def test_second_index_page_contains_three_records(self):
        """На вторую страницу index выводятся оставшиеся 3 поста"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_page_contains_ten_records(self):
        """На первую страницу group_list выводится 10 постов из 13"""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        self.assertEqual(len(response.context['page_obj']), NUM_POSTS)

    def test_second_group_page_contains_three_records(self):
        """На вторую страницу group_list выводятся оставшиеся 3 поста"""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
