from .models import Language, Submission, Task


def get_level_title(level: int) -> str:
    titles = {
        1: "Новичок",
        2: "Стажер",
        3: "Младший разработчик",
        4: "Разработчик",
        5: "Питонист",
        6: "Мастер Python",
        7: "Архитектор",
        8: "Гуру кода",
        9: "Легенда",
    }
    return titles.get(level, f"Уровень {level}")


def user_stats(request):
    data = {
        'active_languages': Language.objects.filter(is_active=True),
        'user_xp': 0,
        'user_streak': 1,
        'user_level': 1,
        'user_level_progress': 0,
        'user_level_title': 'Новичок',
        'solved_tasks_count': 0,
        'total_tasks_count': Task.objects.count(),
    }

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            data['user_xp'] = profile.xp
            data['user_streak'] = profile.streak_days
            data['user_level'] = profile.level
            data['user_level_progress'] = profile.level_progress
            data['user_level_title'] = get_level_title(profile.level)

        data['solved_tasks_count'] = Submission.objects.filter(
            user=request.user,
            status='accepted'
        ).values('task_id').distinct().count()

    return data
