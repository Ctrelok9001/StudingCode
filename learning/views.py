import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Language, Category, Task, TestCase, Submission, Course, Module,
    Lesson, LessonProgress, UserProfile, TaskHintUnlock, Tag,
    QuizQuestion, QuizOption, UserQuizAttempt, CourseCertificate
)
from .runner import execute_python_code, run_test_cases, format_python_code
from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            profile = user.profile
            profile.add_xp(25)

            login(request, user)
            messages.success(request, f"Добро пожаловать на платформу, {user.username}! Вам начислено +25 XP за регистрацию!")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"С возвращением, {user.first_name or user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile)

    submissions = Submission.objects.filter(user=request.user).select_related('task').order_by('-created_at')[:20]
    total_submissions = Submission.objects.filter(user=request.user).count()
    accepted_count = Submission.objects.filter(user=request.user, status='accepted').values('task').distinct().count()
    certificates = CourseCertificate.objects.filter(user=request.user).select_related('course')

    context = {
        'profile': profile,
        'form': form,
        'submissions': submissions,
        'total_submissions': total_submissions,
        'accepted_count': accepted_count,
        'certificates': certificates,
    }
    return render(request, 'learning/profile.html', context)


def home_view(request):
    python_lang = Language.objects.filter(slug='python').first()

    tasks_count = Task.objects.count()
    courses_count = Course.objects.filter(is_published=True).count()
    users_count = User.objects.count()

    recent_tasks = Task.objects.select_related('category').prefetch_related('tags').order_by('number')[:6]
    featured_courses = Course.objects.filter(is_published=True).prefetch_related('modules')[:3]
    top_users = UserProfile.objects.select_related('user').order_by('-xp')[:5]

    solved_task_ids = set()
    if request.user.is_authenticated:
        solved_task_ids = set(
            Submission.objects.filter(user=request.user, status='accepted').values_list('task_id', flat=True)
        )

    context = {
        'python_lang': python_lang,
        'tasks_count': tasks_count,
        'courses_count': courses_count,
        'users_count': users_count,
        'recent_tasks': recent_tasks,
        'featured_courses': featured_courses,
        'top_users': top_users,
        'solved_task_ids': solved_task_ids,
    }
    return render(request, 'learning/home.html', context)


def task_list_view(request):
    tasks_query = Task.objects.select_related('category', 'language').prefetch_related('tags').order_by('number')

    difficulty = request.GET.get('difficulty')
    if difficulty in ['easy', 'medium', 'hard']:
        tasks_query = tasks_query.filter(difficulty=difficulty)

    category_slug = request.GET.get('category')
    if category_slug:
        tasks_query = tasks_query.filter(category__slug=category_slug)

    tag_slug = request.GET.get('tag')
    if tag_slug:
        tasks_query = tasks_query.filter(tags__slug=tag_slug)

    q = request.GET.get('q')
    if q:
        tasks_query = tasks_query.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(number__icontains=q)
        )

    categories = Category.objects.filter(tasks__isnull=False).distinct()
    all_tags = Tag.objects.all()

    solved_task_ids = set()
    attempted_task_ids = set()

    if request.user.is_authenticated:
        user_subs = Submission.objects.filter(user=request.user)
        solved_task_ids = set(user_subs.filter(status='accepted').values_list('task_id', flat=True))
        attempted_task_ids = set(user_subs.values_list('task_id', flat=True)) - solved_task_ids

    tasks_list = []
    for t in tasks_query:
        if t.id in solved_task_ids:
            status = 'solved'
        elif t.id in attempted_task_ids:
            status = 'attempted'
        else:
            status = 'new'
        tasks_list.append({
            'task': t,
            'status': status
        })

    status_filter = request.GET.get('status')
    if status_filter in ['solved', 'attempted', 'new']:
        tasks_list = [item for item in tasks_list if item['status'] == status_filter]

    context = {
        'tasks_list': tasks_list,
        'categories': categories,
        'all_tags': all_tags,
        'current_difficulty': difficulty,
        'current_category': category_slug,
        'current_tag': tag_slug,
        'current_status': status_filter,
        'search_query': q or '',
    }
    return render(request, 'learning/task_list.html', context)


def task_detail_view(request, slug):
    task = get_object_or_404(Task.objects.select_related('language', 'category').prefetch_related('tags'), slug=slug)
    visible_tests = task.test_cases.filter(is_hidden=False)
    hidden_tests_count = task.test_cases.filter(is_hidden=True).count()

    is_solved = False
    is_hint_unlocked = False
    past_submissions = []
    user_initial_code = task.initial_code

    if request.user.is_authenticated:
        user_subs = Submission.objects.filter(user=request.user, task=task)
        is_solved = user_subs.filter(status='accepted').exists()
        is_hint_unlocked = TaskHintUnlock.objects.filter(user=request.user, task=task).exists()
        past_submissions = list(user_subs.order_by('-created_at')[:20])

        latest_sub = past_submissions[0] if past_submissions else None
        if latest_sub:
            user_initial_code = latest_sub.code

    prev_task = Task.objects.filter(language=task.language, number__lt=task.number).order_by('-number').first()
    next_task = Task.objects.filter(language=task.language, number__gt=task.number).order_by('number').first()

    context = {
        'task': task,
        'visible_tests': visible_tests,
        'hidden_tests_count': hidden_tests_count,
        'is_solved': is_solved,
        'is_hint_unlocked': is_hint_unlocked,
        'past_submissions': past_submissions,
        'initial_code': user_initial_code,
        'prev_task': prev_task,
        'next_task': next_task,
    }
    return render(request, 'learning/task_detail.html', context)


@require_POST
def run_code_api(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        stdin_data = data.get('stdin', '')

        result = execute_python_code(code, stdin_data=stdin_data)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def format_code_api(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        success, formatted_or_error = format_python_code(code)
        if success:
            return JsonResponse({'success': True, 'code': formatted_or_error})
        return JsonResponse({'success': False, 'message': formatted_or_error}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def unlock_hint_api(request, slug):
    task = get_object_or_404(Task, slug=slug)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Войдите в систему для открытия подсказки'}, status=401)

    profile = request.user.profile
    already_unlocked = TaskHintUnlock.objects.filter(user=request.user, task=task).exists()

    if not already_unlocked:
        cost = 5
        if profile.xp >= cost:
            profile.xp -= cost
            profile.save()
        TaskHintUnlock.objects.create(user=request.user, task=task)

    return JsonResponse({
        'success': True,
        'hint': task.hints,
        'user_xp': profile.xp
    })


def community_solutions_api(request, slug):
    task = get_object_or_404(Task, slug=slug)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Требуется авторизация.'}, status=403)

    is_solved = Submission.objects.filter(user=request.user, task=task, status='accepted').exists()
    if not is_solved:
        return JsonResponse({'success': False, 'message': 'Сначала успешно решите эту задачу самостоятельно, чтобы увидеть решения сообщества.'}, status=403)

    subs = Submission.objects.filter(task=task, status='accepted').exclude(user=request.user).select_related('user', 'user__profile').order_by('execution_time_ms', '-created_at')[:30]

    seen_users = set()
    solutions_list = []
    for s in subs:
        if s.user_id not in seen_users:
            seen_users.add(s.user_id)
            user_display = s.user.first_name or s.user.username
            user_xp = s.user.profile.xp if hasattr(s.user, 'profile') else 0
            user_level = s.user.profile.level if hasattr(s.user, 'profile') else 1
            solutions_list.append({
                'id': s.id,
                'username': user_display,
                'xp': user_xp,
                'level': user_level,
                'execution_time_ms': s.execution_time_ms,
                'date': s.created_at.strftime('%d.%m.%Y %H:%M'),
                'code': s.code,
            })

    return JsonResponse({'success': True, 'solutions': solutions_list})


@require_POST
def submit_task_api(request, slug):
    task = get_object_or_404(Task, slug=slug)

    try:
        data = json.loads(request.body)
        code = data.get('code', '')

        test_cases = list(task.test_cases.all().order_by('order'))
        judge_res = run_test_cases(code, test_cases)

        xp_gained = 0
        is_first_accepted = False
        submission_data = None

        if request.user.is_authenticated:
            already_solved = Submission.objects.filter(
                user=request.user,
                task=task,
                status='accepted'
            ).exists()

            sub = Submission.objects.create(
                user=request.user,
                task=task,
                code=code,
                status=judge_res['status'],
                tests_passed=judge_res['tests_passed'],
                tests_total=judge_res['total_tests'],
                execution_time_ms=judge_res['duration_ms'],
                error_message=judge_res['error_message'],
            )

            if judge_res['status'] == 'accepted' and not already_solved:
                is_first_accepted = True
                xp_gained = task.xp_reward
                profile = request.user.profile
                profile.add_xp(xp_gained)

            submission_data = {
                'id': sub.id,
                'status': sub.status,
                'status_display': sub.get_status_display(),
                'tests_passed': sub.tests_passed,
                'tests_total': sub.tests_total,
                'execution_time_ms': sub.execution_time_ms,
                'date': sub.created_at.strftime('%d.%m %H:%M'),
                'code': sub.code
            }

        return JsonResponse({
            'success': judge_res['status'] == 'accepted',
            'status': judge_res['status'],
            'status_display': dict(Submission.STATUS_CHOICES).get(judge_res['status'], judge_res['status']),
            'tests_passed': judge_res['tests_passed'],
            'total_tests': judge_res['total_tests'],
            'duration_ms': judge_res['duration_ms'],
            'error_message': judge_res['error_message'],
            'test_results': judge_res['test_results'],
            'xp_gained': xp_gained,
            'is_first_accepted': is_first_accepted,
            'user_xp': request.user.profile.xp if request.user.is_authenticated else 0,
            'user_level': request.user.profile.level if request.user.is_authenticated else 1,
            'reference_solution': task.reference_solution if (judge_res['status'] == 'accepted') else "",
            'submission': submission_data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def check_quiz_api(request):
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        option_id = data.get('option_id')

        question = get_object_or_404(QuizQuestion, id=question_id)
        option = get_object_or_404(QuizOption, id=option_id, question=question)

        is_correct = option.is_correct
        xp_gained = 0

        if is_correct and request.user.is_authenticated:
            attempt, created = UserQuizAttempt.objects.get_or_create(
                user=request.user,
                question=question,
                defaults={'is_passed': True}
            )
            if created or not attempt.is_passed:
                attempt.is_passed = True
                attempt.save()
                xp_gained = question.xp_reward
                request.user.profile.add_xp(xp_gained)

        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'explanation': question.explanation,
            'xp_gained': xp_gained,
            'user_xp': request.user.profile.xp if request.user.is_authenticated else 0
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def courses_list_view(request):
    courses = Course.objects.filter(is_published=True).prefetch_related('modules__lessons')
    return render(request, 'learning/courses_list.html', {'courses': courses})


def course_detail_view(request, slug):
    course = get_object_or_404(Course, slug=slug)
    modules = course.modules.prefetch_related('lessons').order_by('order')

    completed_lesson_ids = set()
    is_course_completed = False
    if request.user.is_authenticated:
        completed_lesson_ids = set(
            LessonProgress.objects.filter(user=request.user, completed=True).values_list('lesson_id', flat=True)
        )
        is_course_completed = course.is_completed_by(request.user)

    context = {
        'course': course,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
        'is_course_completed': is_course_completed,
    }
    return render(request, 'learning/course_detail.html', context)


def course_certificate_view(request, slug):
    course = get_object_or_404(Course, slug=slug)

    if not request.user.is_authenticated:
        messages.warning(request, "Пожалуйста, войдите в систему для просмотра сертификата.")
        return redirect('login')

    if not course.is_completed_by(request.user):
        messages.info(request, "Для получения сертификата необходимо завершить все уроки курса!")
        return redirect('course_detail', slug=course.slug)

    code = f"PYL-{course.id:02d}-{request.user.id:04d}-{uuid.uuid4().hex[:6].upper()}"
    cert, _ = CourseCertificate.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'certificate_code': code}
    )

    context = {
        'course': course,
        'certificate': cert,
        'user': request.user,
    }
    return render(request, 'learning/certificate.html', context)


def lesson_detail_view(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, module__course=course, slug=lesson_slug)

    is_completed = False
    if request.user.is_authenticated:
        progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        if not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()
            request.user.profile.add_xp(lesson.xp_reward)
        is_completed = True

    all_lessons = list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order'))
    current_idx = all_lessons.index(lesson) if lesson in all_lessons else -1
    prev_lesson = all_lessons[current_idx - 1] if current_idx > 0 else None
    next_lesson = all_lessons[current_idx + 1] if current_idx < len(all_lessons) - 1 else None

    quiz_questions = lesson.quiz_questions.prefetch_related('options').all()
    passed_quiz_ids = set()
    if request.user.is_authenticated:
        passed_quiz_ids = set(
            UserQuizAttempt.objects.filter(user=request.user, question__lesson=lesson, is_passed=True).values_list('question_id', flat=True)
        )

    context = {
        'course': course,
        'lesson': lesson,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
        'quiz_questions': quiz_questions,
        'passed_quiz_ids': passed_quiz_ids,
    }
    return render(request, 'learning/lesson_detail.html', context)


def playground_view(request):
    default_code = (
        "fruits = ['Яблоко', 'Банан', 'Манго', 'Апельсин']\n\n"
        "for idx, fruit in enumerate(fruits, 1):\n"
        "    print(f'{idx}. Вкусный {fruit}')\n"
    )
    return render(request, 'learning/playground.html', {'default_code': default_code})


def leaderboard_view(request):
    users = UserProfile.objects.select_related('user').order_by('-xp')[:50]
    return render(request, 'learning/leaderboard.html', {'users': users})


def quick_demo_login(request):
    user, _ = User.objects.get_or_create(
        username="student",
        defaults={"email": "student@example.com", "first_name": "Алексей"}
    )
    login(request, user)
    messages.success(request, f"Вы вошли под тестовой учетной записью {user.username}!")
    return redirect(request.GET.get('next', 'dashboard'))


def user_logout(request):
    logout(request)
    messages.info(request, "Вы вышли из системы. Ждем вас снова!")
    return redirect('home')
