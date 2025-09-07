import csv
import io
import random
import re

from django.shortcuts import render, redirect, get_object_or_404

from .models import Country, QuizRun, Attempt
from .forms import UploadCSVForm, StartQuizForm, AnswerForm

from django.contrib import messages


def home(request):
    return render(request, "home.html")


def upload_countries(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            mode = form.cleaned_data['mode']

            # читаем как UTF-8; если не вышло — даем понятное сообщение
            try:
                f = io.TextIOWrapper(request.FILES['file'].file, encoding='utf-8')
            except Exception:
                messages.error(request, "Не удалось прочитать файл. Пожалуйста, сохраните CSV в кодировке UTF-8.")
                return render(request, "upload.html", {"form": form})

            reader = csv.DictReader(f)
            if not reader.fieldnames:
                messages.warning(request, "Пустой CSV: строки не найдены.")
                return redirect("countries_list")

            headers = [h.strip().lower() for h in reader.fieldnames]
            required = {'name', 'capital'}        # region можно пропускать
            missing = required - set(headers)
            if missing:
                messages.error(
                    request,
                    "Отсутствуют обязательные колонки: {}. Ожидается хотя бы name, capital (region — опционально)."
                    .format(", ".join(sorted(missing)))
                )
                return render(request, "upload.html", {"form": form})

            if mode == 'replace':
                Country.objects.all().delete()

            created = skipped_blank = skipped_dupe_in_file = skipped_existing = 0
            seen_in_file = set()  # для дублей внутри одного CSV по name (без учёта регистра)

            for row in reader:
                name = (row.get('name') or "").strip()
                capital = (row.get('capital') or "").strip()
                region = (row.get('region') or "").strip()

                # пропускаем пустые/некорректные строки
                if not name or not capital:
                    skipped_blank += 1
                    continue

                key = name.lower()
                if key in seen_in_file:
                    skipped_dupe_in_file += 1
                    continue
                seen_in_file.add(key)

                if mode == 'append':
                    # не перезаписываем существующие, просто пропускаем дубли по name (без учёта регистра)
                    if Country.objects.filter(name__iexact=name).exists():
                        skipped_existing += 1
                        continue
                    Country.objects.create(name=name, capital=capital, region=region)
                    created += 1
                else:
                    # replace: мы очистили справочник; можно просто создавать
                    Country.objects.create(name=name, capital=capital, region=region)
                    created += 1

            messages.success(
                request,
                f"Импорт завершён. Добавлено: {created}. "
                f"Пропущено пустых/некорректных: {skipped_blank}. "
                f"Дубликатов в файле: {skipped_dupe_in_file}. "
                f"Существующих в базе (при добавлении): {skipped_existing}."
            )
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
            direction = form.cleaned_data['direction']
            region = form.cleaned_data['region']
            requested_total = form.cleaned_data['total']

            # считаем доступные вопросы с учётом региона
            qs = Country.objects.all()
            if region:
                qs = qs.filter(region__iexact=region)
            available = qs.count()

            if available == 0:
                messages.warning(
                    request,
                    "В выбранном регионе пока нет данных. Загрузите CSV или выберите «Любой регион»."
                )
                return render(request, "start.html", {"form": form})

            # клампим total
            total = min(requested_total, available)
            if total < requested_total:
                messages.info(
                    request,
                    f"Запрошено {requested_total} вопросов, но доступно только {available}. "
                    f"Установлено {total}."
                )

            quiz = QuizRun.objects.create(
                direction=direction,
                total=total,
                region=region,
            )
            request.session['quiz_id'] = quiz.id
            request.session['asked_ids'] = []
            request.session.pop('current_cid', None)
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

    available_now = qs.count()

    if quiz.total > available_now:
        quiz.total = available_now
        quiz.save(update_fields=['total'])

    def check_correct(quiz_mode, ans, country):
        def re_sub(string):
            return re.sub('[^a-z]', '', string.lower())

        return (
            (quiz_mode == 'c2cap' and re_sub(ans) == re_sub(country.capital)) or
            (quiz_mode == 'cap2c' and re_sub(ans) == re_sub(country.name))
        )

    remaining = list(qs.exclude(id__in=asked).values_list('id', flat=True))
    if not remaining or Attempt.objects.filter(quiz=quiz).count() >= quiz.total:
        return redirect("results")

    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            cid = form.cleaned_data['cid']
            country = Country.objects.get(id=cid)

            ans = form.cleaned_data['answer'].strip()
            correct = check_correct(quiz.direction, ans, country)
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

    answered = list(
            Attempt.objects
            .filter(quiz=quiz)
            .order_by('created_at')
            .values_list('is_correct', flat=True)
        )
    remaining = max(quiz.total - len(answered), 0)
    
    prompt = country.name if quiz.direction == 'c2cap' else country.capital
    task = "Назовите столицу" if quiz.direction == 'c2cap' else "Назовите страну"
    return render(
            request,
            "question.html",
            {
                "form": form,
                "prompt": prompt,
                "quiz": quiz,
                "answered": answered,
                "remaining_range": range(remaining),
            },
        )

def results(request):
    quiz_id = request.session.get('quiz_id')
    quiz = get_object_or_404(QuizRun, id=quiz_id)
    attempts = Attempt.objects.filter(quiz=quiz)
    return render(request, "results.html", {"quiz": quiz, "attempts": attempts})
