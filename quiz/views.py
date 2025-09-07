import csv, io, random
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Country, QuizRun, Attempt
from .forms import UploadCSVForm, StartQuizForm, AnswerForm


def home(request):
    return render(request, "home.html")


def upload_countries(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            f = io.TextIOWrapper(request.FILES['file'].file, encoding='utf-8')
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('name','').strip()
                capital = row.get('capital','').strip()
                region = row.get('region','').strip()
                print('asjasjj success')
                if name and capital:
                    Country.objects.update_or_create(name=name, defaults={'capital': capital, 'region': region})
            return redirect("countries_list")
    else:
        form = UploadCSVForm()
    return render(request, "upload.html", {"form": form})


def countries_list(request):
    items = Country.objects.all().order_by('name')
    return render(request, "countries_list.html", {"items": items})


def start_quiz(request):
    if request.method == "POST":
        form = StartQuizForm(request.POST)
        if form.is_valid():
            quiz = QuizRun.objects.create(
                direction=form.cleaned_data['direction'],
                total=form.cleaned_data['total'],
                region=form.cleaned_data['region'],
            )
            request.session['quiz_id'] = quiz.id
            request.session['asked_ids'] = []
            return redirect("question")
    else:
        form = StartQuizForm()
    return render(request, "start.html", {"form": form})


def question(request):
    quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(QuizRun, id=quiz_id)

    asked = set(request.session.get('asked_ids', []))
    qs = Country.objects.all()
    if quiz.region:
        qs = qs.filter(region__iexact=quiz.region)

    remaining = list(qs.exclude(id__in=asked).values_list('id', flat=True))
    if not remaining or Attempt.objects.filter(quiz=quiz).count() >= quiz.total:
        return redirect("results")

    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            cid = form.cleaned_data['cid']
            country = Country.objects.get(id=cid)

            ans = form.cleaned_data['answer'].strip()
            correct = (
                (quiz.direction == 'c2cap' and ans.lower() == country.capital.lower()) or
                (quiz.direction == 'cap2c' and ans.lower() == country.name.lower())
            )
            Attempt.objects.create(quiz=quiz, country=country, user_answer=ans, is_correct=correct)
            if correct:
                quiz.correct += 1
                quiz.save(update_fields=['correct'])
            quiz.current_num += 1
            quiz.save(update_fields=['current_num'])
            asked.add(country.id)
            request.session['asked_ids'] = list(asked)
            return redirect("question")
    else:
        remaining = list(qs.exclude(id__in=asked).values_list('id', flat=True))
        if not remaining:
            return redirect("results")
        cid = random.choice(remaining)
        country = Country.objects.get(id=cid)
        form = AnswerForm(initial={'cid': cid})

    prompt = country.name if quiz.direction == 'c2cap' else country.capital
    question = "Назовите столицу" if quiz.direction == 'c2cap' else "Назовите страну"
    return render(request, "question.html", {"form": form, "prompt": prompt, "question": question, "quiz": quiz})

def results(request):
    quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(QuizRun, id=quiz_id)
    attempts = Attempt.objects.filter(quiz=quiz)
    return render(request, "results.html", {"quiz": quiz, "attempts": attempts})
