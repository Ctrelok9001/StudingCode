import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='status',
            field=models.CharField(choices=[('accepted', 'Решено (Accepted)'), ('wrong_answer', 'Неверный ответ (Wrong Answer)'), ('syntax_error', 'Синтаксическая ошибка (Syntax Error)'), ('runtime_error', 'Ошибка выполнения (Runtime Error)'), ('security_error', 'Заблокировано (Security Error)'), ('timeout', 'Превышен лимит времени (Time Limit)')], max_length=20, verbose_name='Статус'),
        ),
        migrations.CreateModel(
            name='TaskHintUnlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время разблокировки')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_hints', to='learning.task', verbose_name='Задача')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocked_hints', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Разблокированная подсказка',
                'verbose_name_plural': 'Разблокированные подсказки',
                'unique_together': {('user', 'task')},
            },
        ),
    ]
