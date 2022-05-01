from django import forms

from .models import Post, Group, Comment


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)
    group = forms.ModelChoiceField(queryset=Group.objects.all(),
                                   required=False)
    image = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        label = {
            'text': 'Текст поста',
            'group': 'Группа поста',
            'image': 'Изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        label = {
            'text': 'Комментарий к посту'
        }
