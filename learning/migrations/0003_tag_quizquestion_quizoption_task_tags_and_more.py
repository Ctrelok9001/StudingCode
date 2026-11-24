import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_alter_submission_status_taskhintunlock'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Название тега')),
                ('slug', models.SlugField(unique=True)),
                ('color', models.CharField(default='sky', max_length=30, verbose_name='Цветовая схема')),
            ],
            options={
                'verbose_name': 'Тег темы',
                'verbose_name_plural': 'Теги тем',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='QuizQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField(verbose_name='Текст вопроса')),
                ('explanation', models.TextField(blank=True, verbose_name='Объяснение правильного ответа')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('xp_reward', models.PositiveIntegerField(default=5, verbose_name='Награда (XP)')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_questions', to='learning.lesson', verbose_name='Урок')),
            ],
            options={
                'verbose_name': 'Вопрос квиза',
                'verbose_name_plural': 'Вопросы квиза',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='QuizOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Вариант ответа')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильный ответ')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='learning.quizquestion', verbose_name='Вопрос')),
            ],
            options={
                'verbose_name': 'Вариант ответа',
                'verbose_name_plural': 'Варианты ответа',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='task',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tasks', to='learning.tag', verbose_name='Теги темы'),
        ),
        migrations.CreateModel(
            name='CourseCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate_code', models.CharField(max_length=40, unique=True, verbose_name='Код сертификата')),
                ('issued_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='learning.course', verbose_name='Курс')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Сертификат курса',
                'verbose_name_plural': 'Сертификаты курсов',
                'unique_together': {('user', 'course')},
            },
        ),
        migrations.CreateModel(
            name='UserQuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_passed', models.BooleanField(default=False, verbose_name='Пройден')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время прохождения')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='learning.quizquestion', verbose_name='Вопрос')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Попытка прохождения квиза',
                'verbose_name_plural': 'Попытки прохождения квиза',
                'unique_together': {('user', 'question')},
            },
        ),
    ]
