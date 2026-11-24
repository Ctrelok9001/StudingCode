import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Язык")
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, default="python", help_text="Иконка или класс", verbose_name="Иконка")
    color = models.CharField(max_length=30, default="#3b82f6", verbose_name="Цвет акцента")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Язык программирования"
        verbose_name_plural = "Языки программирования"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Category(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='categories', verbose_name="Язык")
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Категория задач"
        verbose_name_plural = "Категории задач"
        ordering = ['order', 'id']
        unique_together = ('language', 'slug')

    def __str__(self):
        return f"{self.language.name} - {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=30, default="sky", verbose_name="Цветовая схема")

    class Meta:
        verbose_name = "Тег темы"
        verbose_name_plural = "Теги тем"
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий (Easy)'),
        ('medium', 'Средний (Medium)'),
        ('hard', 'Сложный (Hard)'),
    ]

    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='tasks', verbose_name="Язык")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="Категория")
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks', verbose_name="Теги темы")
    number = models.PositiveIntegerField(default=1, verbose_name="Номер задачи")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy', verbose_name="Сложность")
    description = models.TextField(verbose_name="Условие задачи (Markdown/HTML)")
    input_format = models.TextField(blank=True, verbose_name="Формат входных данных")
    output_format = models.TextField(blank=True, verbose_name="Формат выходных данных")
    initial_code = models.TextField(blank=True, default="# Напишите ваше решение здесь\n", verbose_name="Начальный шаблон кода")
    hints = models.TextField(blank=True, verbose_name="Подсказки")
    reference_solution = models.TextField(blank=True, verbose_name="Эталонное решение")
    xp_reward = models.PositiveIntegerField(default=20, verbose_name="Награда (XP)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['number', 'id']

    def __str__(self):
        return f"№{self.number}. {self.title} ({self.get_difficulty_display()})"

    @property
    def total_submissions_count(self):
        return self.submissions.count()

    @property
    def accepted_submissions_count(self):
        return self.submissions.filter(status='accepted').count()

    @property
    def acceptance_rate(self):
        total = self.total_submissions_count
        if total == 0:
            return 100.0
        accepted = self.accepted_submissions_count
        return round((accepted / total) * 100, 1)


class TestCase(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='test_cases', verbose_name="Задача")
    input_data = models.TextField(blank=True, verbose_name="Входные данные (stdin)")
    expected_output = models.TextField(verbose_name="Ожидаемый вывод (stdout)")
    is_hidden = models.BooleanField(default=False, verbose_name="Скрытый тест (не виден пользователю)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Тестовый пример"
        verbose_name_plural = "Тестовые примеры"
        ordering = ['order', 'id']

    def __str__(self):
        hidden_mark = " (Скрытый)" if self.is_hidden else ""
        return f"Тест #{self.order + 1} для {self.task.title}{hidden_mark}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Решено (Accepted)'),
        ('wrong_answer', 'Неверный ответ (Wrong Answer)'),
        ('syntax_error', 'Синтаксическая ошибка (Syntax Error)'),
        ('runtime_error', 'Ошибка выполнения (Runtime Error)'),
        ('security_error', 'Заблокировано (Security Error)'),
        ('timeout', 'Превышен лимит времени (Time Limit)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', verbose_name="Пользователь")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions', verbose_name="Задача")
    code = models.TextField(verbose_name="Код решения")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    tests_passed = models.PositiveIntegerField(default=0, verbose_name="Пройдено тестов")
    tests_total = models.PositiveIntegerField(default=0, verbose_name="Всего тестов")
    execution_time_ms = models.PositiveIntegerField(default=0, verbose_name="Время выполнения (мс)")
    output = models.TextField(blank=True, verbose_name="Вывод программы")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")

    class Meta:
        verbose_name = "Попытка решения"
        verbose_name_plural = "Попытки решения"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.task.title} [{self.get_status_display()}]"


class TaskHintUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_hints', verbose_name="Пользователь")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='unlocked_hints', verbose_name="Задача")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время разблокировки")

    class Meta:
        verbose_name = "Разблокированная подсказка"
        verbose_name_plural = "Разблокированные подсказки"
        unique_together = ('user', 'task')

    def __str__(self):
        return f"{self.user.username} -> {self.task.title}"


class Course(models.Model):
    LEVEL_CHOICES = [
        ('novice', 'Новичок'),
        ('intermediate', 'Базовый / Средний'),
        ('advanced', 'Продвинутый'),
    ]

    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='courses', verbose_name="Язык")
    title = models.CharField(max_length=200, verbose_name="Название курса")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(verbose_name="Описание курса")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='novice', verbose_name="Уровень")
    estimated_time = models.CharField(max_length=50, default="30 мин", verbose_name="Расчетное время")
    xp_total = models.PositiveIntegerField(default=100, verbose_name="Всего XP")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")

    class Meta:
        verbose_name = "Курс / Трек"
        verbose_name_plural = "Курсы / Треки"
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

    def is_completed_by(self, user):
        if not user or not user.is_authenticated:
            return False
        lesson_ids = list(Lesson.objects.filter(module__course=self).values_list('id', flat=True))
        if not lesson_ids:
            return False
        completed_count = LessonProgress.objects.filter(user=user, lesson_id__in=lesson_ids, completed=True).count()
        return completed_count >= len(lesson_ids)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name="Курс")
    title = models.CharField(max_length=200, verbose_name="Название модуля")
    description = models.TextField(blank=True, verbose_name="Описание модуля")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name="Модуль")
    title = models.CharField(max_length=200, verbose_name="Название урока")
    slug = models.SlugField(max_length=200)
    content = models.TextField(verbose_name="Теория / Содержание урока")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons', verbose_name="Связанная практическая задача")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    xp_reward = models.PositiveIntegerField(default=15, verbose_name="XP за урок")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['order', 'id']
        unique_together = ('module', 'slug')

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class QuizQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quiz_questions', verbose_name="Урок")
    question = models.TextField(verbose_name="Текст вопроса")
    explanation = models.TextField(blank=True, verbose_name="Объяснение правильного ответа")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    xp_reward = models.PositiveIntegerField(default=5, verbose_name="Награда (XP)")

    class Meta:
        verbose_name = "Вопрос квиза"
        verbose_name_plural = "Вопросы квиза"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.lesson.title}: {self.question[:50]}"


class QuizOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options', verbose_name="Вопрос")
    text = models.CharField(max_length=255, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        ordering = ['order', 'id']

    def __str__(self):
        correct_mark = " (Верно)" if self.is_correct else ""
        return f"{self.text}{correct_mark}"


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', verbose_name="Пользователь")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, verbose_name="Вопрос")
    is_passed = models.BooleanField(default=False, verbose_name="Пройден")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время прохождения")

    class Meta:
        verbose_name = "Попытка прохождения квиза"
        verbose_name_plural = "Попытки прохождения квиза"
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} -> {self.question_id}"


class CourseCertificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates', verbose_name="Пользователь")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates', verbose_name="Курс")
    certificate_code = models.CharField(max_length=40, unique=True, verbose_name="Код сертификата")
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")

    class Meta:
        verbose_name = "Сертификат курса"
        verbose_name_plural = "Сертификаты курсов"
        unique_together = ('user', 'course')

    def __str__(self):
        return f"Сертификат {self.certificate_code} ({self.user.username} - {self.course.title})"


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    xp = models.PositiveIntegerField(default=0, verbose_name="Очки опыта (XP)")
    streak_days = models.PositiveIntegerField(default=1, verbose_name="Серия дней (Streak)")
    last_activity_date = models.DateField(default=timezone.now, verbose_name="Дата последней активности")
    avatar = models.CharField(max_length=100, default="cat", verbose_name="Аватар")
    bio = models.TextField(blank=True, default="Учусь программировать на Python!", verbose_name="О себе")

    def __str__(self):
        return f"{self.user.username} ({self.xp} XP)"

    @property
    def level(self):
        return (self.xp // 100) + 1

    @property
    def level_progress(self):
        return self.xp % 100

    def add_xp(self, amount):
        today = timezone.now().date()
        last_date = self.last_activity_date
        if hasattr(last_date, 'date'):
            last_date = last_date.date()
        if last_date is None or last_date < today:
            if last_date is not None:
                delta = (today - last_date).days
                if delta == 1:
                    self.streak_days += 1
                elif delta > 1:
                    self.streak_days = 1
            self.last_activity_date = today
        self.xp += amount
        self.save()
