from django import forms
from django.core.exceptions import ValidationError
from Apps.extras.models import Reviews


class ReviewForm(forms.ModelForm):
    """Форма для добавления отзыва о товаре"""
    
    class Meta:
        model = Reviews
        fields = ['reviews_rating', 'reviews_comment']
        widgets = {
            'reviews_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'step': 1,
            }),
            'reviews_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Оставьте ваш отзыв о товаре...'
            }),
        }
        labels = {
            'reviews_rating': 'Оценка',
            'reviews_comment': 'Отзыв',
        }
        help_texts = {
            'reviews_rating': 'Выберите оценку от 1 до 5 звезд',
            'reviews_comment': 'Расскажите о вашем опыте использования товара',
        }
    
    def clean_reviews_rating(self):
        rating = self.cleaned_data.get('reviews_rating')
        if rating is None:
            raise ValidationError('Необходимо указать оценку.')
        if rating < 1 or rating > 5:
            raise ValidationError('Оценка должна быть от 1 до 5 звезд.')
        return rating
    
    def clean_reviews_comment(self):
        comment = self.cleaned_data.get('reviews_comment', '').strip()
        if not comment:
            raise ValidationError('Необходимо оставить комментарий.')
        if len(comment) < 10:
            raise ValidationError('Комментарий должен содержать минимум 10 символов.')
        if len(comment) > 2000:
            raise ValidationError('Комментарий не должен превышать 2000 символов.')
        return comment
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы Bootstrap к полям
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')

