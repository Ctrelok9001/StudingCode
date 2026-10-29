import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import Language, Category, Task, TestCase, Submission, Course, Module, Lesson, LessonProgress, UserProfile
from .runner import execute_python_code, run_test_cases
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
            messages.success(request, f"Добро пожаловать на платформу, {user.username}! Вам начислено +25 XP за регистрацию 🎉")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next', 'dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"С возвращением, {user.first_name or user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Неверный логин или пароль. Пожалуйста, проверьте данные.")
    else:
        form = UserLoginForm()

    return render(request, 'registration/login.html', {'form': form, 'next': next_url})


@login_required
def profile_view(request):
    profile = request.user.profile
    submissions = Submission.objects.filter(user=request.user).select_related('task').order_by('-created_at')[:20]

    solved_submissions = Submission.objects.filter(user=request.user, status='accepted').values('task_id').distinct()
    solved_count = solved_submissions.count()

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.save()
            messages.success(request, "Профиль успешно обновлен!")
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'email': request.user.email,
        })

    context = {
        'profile': profile,
        'submissions': submissions,
        'solved_count': solved_count,
        'form': form,
    }
    return render(request, 'learning/profile.html', context)


def home_view(request):
    python_lang = Language.objects.filter(slug='python').first()
    categories = Category.objects.filter(language=python_lang).annotate(
        task_count=Count('tasks')
    )
    courses = Course.objects.filter(language=python_lang, is_published=True).prefetch_related('modules__lessons')

    recent_tasks = Task.objects.filter(language=python_lang)[:4]

    top_users = UserProfile.objects.select_related('user').order_by('-xp')[:5]

    solved_task_ids = set()
    if request.user.is_authenticated:
        solved_task_ids = set(
            Submission.objects.filter(user=request.user, status='accepted').values_list('task_id', flat=True)
        )

    context = {
        'python_lang': python_lang,
        'categories': categories,
        'courses': courses,
        'recent_tasks': recent_tasks,
        'top_users': top_users,
        'solved_task_ids': solved_task_ids,
    }
    return render(request, 'learning/home.html', context)


def task_list_view(request):
    python_lang = Language.objects.filter(slug='python').first()
    tasks_query = Task.objects.filter(language=python_lang).select_related('category')

    category_slug = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search_query = request.GET.get('q')

    if category_slug:
        tasks_query = tasks_query.filter(category__slug=category_slug)
    if difficulty:
        tasks_query = tasks_query.filter(difficulty=difficulty)
    if search_query:
        tasks_query = tasks_query.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    tasks = list(tasks_query.order_by('number'))

    solved_task_ids = set()
    attempted_task_ids = set()
    if request.user.is_authenticated:
        submissions = Submission.objects.filter(user=request.user)
        for s in submissions:
            attempted_task_ids.add(s.task_id)
            if s.status == 'accepted':
                solved_task_ids.add(s.task_id)

    for task in tasks:
        if task.id in solved_task_ids:
            task.user_status = 'solved'
        elif task.id in attempted_task_ids:
            task.user_status = 'attempted'
        else:
            task.user_status = 'new'

    categories = Category.objects.filter(language=python_lang).annotate(count=Count('tasks'))

    total_tasks = len(tasks)
    solved_count = len(solved_task_ids)
    progress_pct = int((solved_count / max(total_tasks, 1)) * 100)

    context = {
        'tasks': tasks,
        'categories': categories,
        'current_category': category_slug,
        'current_difficulty': difficulty,
        'search_query': search_query,
        'total_tasks': total_tasks,
        'solved_count': solved_count,
        'progress_pct': progress_pct,
    }
    return render(request, 'learning/task_list.html', context)


def task_detail_view(request, slug):
    task = get_object_or_404(Task.objects.select_related('language', 'category'), slug=slug)
    visible_tests = task.test_cases.filter(is_hidden=False)
    hidden_tests_count = task.test_cases.filter(is_hidden=True).count()

    is_solved = False
    past_submissions = []
    user_initial_code = task.initial_code

    if request.user.is_authenticated:
        user_subs = Submission.objects.filter(user=request.user, task=task)
        is_solved = user_subs.filter(status='accepted').exists()
        past_submissions = user_subs.order_by('-created_at')[:10]

        latest_sub = past_submissions.first()
        if latest_sub:
            user_initial_code = latest_sub.code

    prev_task = Task.objects.filter(language=task.language, number__lt=task.number).order_by('-number').first()
    next_task = Task.objects.filter(language=task.language, number__gt=task.number).order_by('number').first()

    context = {
        'task': task,
        'visible_tests': visible_tests,
        'hidden_tests_count': hidden_tests_count,
        'is_solved': is_solved,
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
def submit_task_api(request, slug):
    task = get_object_or_404(Task, slug=slug)

    try:
        data = json.loads(request.body)
        code = data.get('code', '')

        test_cases = list(task.test_cases.all().order_by('order'))
        judge_res = run_test_cases(code, test_cases)

        xp_gained = 0
        is_first_accepted = False

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
    if request.user.is_authenticated:
        completed_lesson_ids = set(
            LessonProgress.objects.filter(user=request.user, completed=True).values_list('lesson_id', flat=True)
        )

    context = {
        'course': course,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
    }
    return render(request, 'learning/course_detail.html', context)


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

    context = {
        'course': course,
        'lesson': lesson,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
    }
    return render(request, 'learning/lesson_detail.html', context)


def playground_view(request):
    default_code = (
        "# Интерактивная песочница Python\n"
        "# Пишите любой код и запускайте его прямо в браузере!\n\n"
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
