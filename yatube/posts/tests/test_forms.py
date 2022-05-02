import os

import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый юзер')
        cls.commentator = User.objects.create_user(
            username='Тестовый комментатор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.edit_post = Post.objects.create(
            text='Отредактированный пост',
            author=cls.user,
            group=cls.group2,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.commentator,
            text='Текст тестового комментария',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_commentator = Client()
        self.authorized_commentator.force_login(self.commentator)

    def test_post_saved(self):
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
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.latest('id')
        last_post_image_name = os.path.basename(last_post.image.name)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.user.username}))
        self.assertEqual(last_post.author.id, self.post.author.id)
        self.assertEqual(last_post.group.pk, form_data['group'])
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post_image_name, form_data['image'].name)

    def test_post_edited(self):
        form_data = {
            'text': self.edit_post.text,
            'group': self.edit_post.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.edit_post.pk}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=self.edit_post.pk)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.edit_post.pk}))
        self.assertEqual(edited_post, self.edit_post)
        self.assertEqual(edited_post.group.pk, form_data['group'])
        self.assertEqual(edited_post.text, form_data['text'])

    def test_add_comment(self):
        form_data = {
            'text': self.comment.text,
        }
        self.authorized_commentator.post(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        created_comment = Comment.objects.get(post_id=self.post.pk)
        self.assertEqual(created_comment.text, form_data['text'])
