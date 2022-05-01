import tempfile
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms

from posts.views import PAGE_NMB
from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый юзер')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, test_object):
        test_object = Post.objects.latest('id')
        self.assertEqual(test_object.pk, self.post.pk)
        self.assertEqual(test_object.text, self.post.text)
        self.assertEqual(test_object.author.id, self.user.id)
        self.assertEqual(test_object.group, self.post.group)

    def test_views_use_correct_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_object = response.context['page_obj'][0]
        self.check_post(test_object)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}))
        first_object = response.context['group']
        title_1 = first_object.title
        slug_1 = first_object.slug
        self.assertEqual(title_1, self.post.group.title)
        self.assertEqual(slug_1, self.group.slug)

    def test_profile_detail_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(reverse(
                'posts:profile', kwargs={'username': self.user.username})))
        test_object = response.context['page_obj'][0]
        self.check_post(test_object)

    def test_post_detail_pages_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].author.username,
                         self.user.username)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый юзер')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(1, 14):
            Post.objects.create(
                text=f'Тестовый пост{i}',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), PAGE_NMB)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         Post.objects.count() - PAGE_NMB)

    def test_group_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), PAGE_NMB)

    def test_second_group_page_contains_three_records(self):
        response = (self.authorized_client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']),
                         Post.objects.count() - PAGE_NMB)

    def test_profile_page_contains_ten_records(self):
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})))
        self.assertEqual(len(response.context['page_obj']), PAGE_NMB)

    def test_second_profile_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         Post.objects.count() - PAGE_NMB)


class CommentTest(TestCase):
    """Проверка комментариев"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='post_author')
        cls.commentator = User.objects.create_user(username='commentator')
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый текст',
            )

    def setUp(self):
        self.author_user_client = Client()
        self.author_user_client.force_login(self.author_user)
        self.commentator_client = Client()
        self.commentator_client.force_login(self.commentator)
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.commentator,
            text='Тестовый комментарий',
        )

    def test_comment_appear(self):
        response = self.commentator_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comment = response.context['comments'][0]
        text = comment.text
        self.assertEqual(text, self.comment.text)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый юзер')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        self.pages = {
            reverse('posts:index'): 'Главная страница',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 'Страница группы',
            reverse('posts:profile', kwargs={
                    'username': self.user.username}): 'Профиль пользователя',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_content_contains_image(self):
        """Проверка вывода в контексте картинки на страницы index, group_list
        profile.
        """
        for reverse_name in self.pages.keys():
            response = self.authorized_client.get(reverse_name)
            image_file = response.context['page_obj'][0].image
            self.assertEqual(image_file, 'posts/small.gif')


class CashTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='Тестовый юзер')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст'
        )

    def test_of_caching(self):
        """Проверка кэшинга index."""
        response = self.authorized_client.get(reverse('posts:index'))
        new_content = response.content
        Post.objects.filter(id=self.post.pk).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        content_after_delete = response.content
        self.assertEqual(new_content, content_after_delete)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        content_after_clear = response.content
        self.assertNotEqual(content_after_clear, new_content)


class FollowerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(
            username='Тестовый автор')
        cls.follow_user = User.objects.create_user(
            username='Тестовый подписчик')
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый текст',
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author_user)
        self.follow_client = Client()
        self.follow_client.force_login(self.follow_user)

    def test_follow_user_to_author(self):
        """Проверка подписки и отписки на авторов."""
        self.follow_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.author_user.username}))
        follow = Follow.objects.filter(
            user=self.follow_user, author=self.author_user).exists()
        self.assertTrue(follow)
        self.follow_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.author_user.username}))
        follow = Follow.objects.filter(
            user=self.follow_user, author=self.author_user).exists()
        self.assertEqual(follow, False)

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.follow_user, author=self.author_user)
        response = self.follow_client.get(reverse('posts:follow_index'))
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, 'Тестовый текст')
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, 'Тестовый текст')
