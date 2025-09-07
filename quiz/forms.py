from django import forms
from .models import Country


class UploadCSVForm(forms.Form):
    file = forms.FileField(help_text="CSV с колонками: name,capital,region")


class StartQuizForm(forms.Form):
    direction = forms.ChoiceField(
        choices=[('c2cap','Страна→Столица'), ('cap2c','Столица→Страна')],
        label='Режим игры'
    )
    region = forms.ChoiceField(choices=[], required=False, label='Регион')
    total = forms.IntegerField(min_value=1, max_value=999999, initial=10, label='Количество вопросов')

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
    answer = forms.CharField()
