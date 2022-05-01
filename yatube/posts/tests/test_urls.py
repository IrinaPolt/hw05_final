from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, Follow

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='any')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages(self):
        cases = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

        for url, template in cases.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Если пользователь запрашивает url, который не существует"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response=response,
                                template_name='core/404.html')

    def test_post_edit_template_author(self):
        """Автор поста может его редактировать."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response=response,
                                template_name='posts/create_post.html')

    def test_post_edit_template_not_author(self):
        """Пользователь, не являющийся автором поста,
        не имеет доступа к странице редактирования.
        """
        response = self.client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_guest(self):
        """Незарегистрированный пользователь не может создать пост"""
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class RedirectURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый юзер')
        cls.author = User.objects.create_user(username='Тестовый автор')
        cls.guest_client = Client()
        cls.authorized_client = Client()

    def setUp(self) -> None:
        super().setUp()
        self.authorized_client.force_login(user=self.user)
        self.post = Post.objects.create(
            text='Тестовый пост', author=self.author)
        self.url = reverse('posts:profile_follow',
                           kwargs={'username': self.author.username})

    def test_get_pages(self):
        print(self.url)
        response = self.authorized_client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), 1)
