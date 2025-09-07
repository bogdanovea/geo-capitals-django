from django import forms

class UploadCSVForm(forms.Form):
    file = forms.FileField(help_text="CSV с колонками: name,capital,region")

class StartQuizForm(forms.Form):
    direction = forms.ChoiceField(choices=[('c2cap','Страна→Столица'),('cap2c','Столица→Страна')])
    region = forms.CharField(required=False)
    total = forms.IntegerField(min_value=1, max_value=50, initial=10)

class AnswerForm(forms.Form):
    answer = forms.CharField()
