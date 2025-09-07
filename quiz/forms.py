from django import forms
from .models import Country  # если уже есть импорт — не дублируйте

class UploadCSVForm(forms.Form):
    file = forms.FileField(help_text="CSV с колонками: name,capital,region")
    mode = forms.ChoiceField(
        label="Режим загрузки",
        choices=[
            ('append', 'Добавить (без дублей)'),
            ('replace', 'Заменить существующие (очистить справочник)'),
        ],
        initial='append',
        widget=forms.RadioSelect
    )

class StartQuizForm(forms.Form):
    direction = forms.ChoiceField(
        choices=[('c2cap','Страна→Столица'), ('cap2c','Столица→Страна')],
        label='Направление'
    )
    region = forms.ChoiceField(choices=[], required=False, label='Регион')
    total = forms.IntegerField(min_value=1, max_value=50, initial=10, label='Количество вопросов')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        regions_qs = (Country.objects
                      .exclude(region__isnull=True)
                      .exclude(region__exact='')
                      .values_list('region', flat=True)
                      .distinct()
                      .order_by('region'))
        choices = [('', 'Любой регион')] + [(r, r) for r in regions_qs]
        self.fields['region'].choices = choices

class AnswerForm(forms.Form):
    cid = forms.IntegerField(widget=forms.HiddenInput())
    answer = forms.CharField(
        label='Ответ',
        widget=forms.TextInput(attrs={'placeholder': 'Введите ответ', 'autocomplete': 'off'})
    )