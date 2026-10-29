from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning.models import Language, Category, Task, TestCase, Course, Module, Lesson, UserProfile


class Command(BaseCommand):
    help = "Заполняет базу данных начальными языками, курсами и практическими задачами по Python"

    def handle(self, *args, **options):
        self.stdout.write("Начало инициализации данных...")

        demo_user, created = User.objects.get_or_create(
            username="student",
            defaults={"email": "student@example.com", "first_name": "Алексей"}
        )
        if created:
            demo_user.set_password("student123")
            demo_user.save()
            demo_user.profile.xp = 45
            demo_user.profile.streak_days = 3
            demo_user.profile.save()
            self.stdout.write("Создан демо-пользователь: student / student123")

        py_lang, _ = Language.objects.get_or_create(
            slug="python",
            defaults={
                "name": "Python",
                "icon": "fa-brands fa-python",
                "color": "#3b82f6",
                "description": "Самый популярный современный язык программирования для веба, анализа данных, машинного обучения и скриптов.",
                "is_active": True,
                "order": 1
            }
        )

        js_lang, _ = Language.objects.get_or_create(
            slug="javascript",
            defaults={
                "name": "JavaScript",
                "icon": "fa-brands fa-js",
                "color": "#eab308",
                "description": "Язык интерактивности веб-страниц, браузерных приложений и серверного бэкенда на Node.js.",
                "is_active": False,
                "order": 2
            }
        )

        go_lang, _ = Language.objects.get_or_create(
            slug="golang",
            defaults={
                "name": "Go",
                "icon": "fa-brands fa-golang",
                "color": "#06b6d4",
                "description": "Производительный язык от Google для микросервисов, распределенных систем и облачной инфраструктуры.",
                "is_active": False,
                "order": 3
            }
        )

        sql_lang, _ = Language.objects.get_or_create(
            slug="sql",
            defaults={
                "name": "SQL",
                "icon": "fa-solid fa-database",
                "color": "#6366f1",
                "description": "Декларативный язык управления реляционными базами данных (PostgreSQL, MySQL, SQLite).",
                "is_active": False,
                "order": 4
            }
        )

        cat_basics, _ = Category.objects.get_or_create(
            language=py_lang, slug="basics",
            defaults={"name": "Базовый синтаксис и ввод/вывод", "order": 1, "description": "Знакомство с print(), input() и типами данных"}
        )
        cat_conditions, _ = Category.objects.get_or_create(
            language=py_lang, slug="conditions",
            defaults={"name": "Условия и логика (if/elif/else)", "order": 2, "description": "Ветвления, логические операторы and, or, not"}
        )
        cat_loops, _ = Category.objects.get_or_create(
            language=py_lang, slug="loops",
            defaults={"name": "Циклы (for и while)", "order": 3, "description": "Повторение операций, break, continue, range()"}
        )
        cat_strings, _ = Category.objects.get_or_create(
            language=py_lang, slug="strings",
            defaults={"name": "Строки и форматирование (f-strings)", "order": 4, "description": "Методы строк, срезы, современные f-строки"}
        )
        cat_lists, _ = Category.objects.get_or_create(
            language=py_lang, slug="lists",
            defaults={"name": "Списки и коллекции", "order": 5, "description": "Срезы списков, списковые включения (list comprehensions), сортировка"}
        )
        cat_functions, _ = Category.objects.get_or_create(
            language=py_lang, slug="functions",
            defaults={"name": "Функции и лямбды", "order": 6, "description": "Определение функций, аргументы, возврат значений, lambda"}
        )
        cat_algorithms, _ = Category.objects.get_or_create(
            language=py_lang, slug="algorithms",
            defaults={"name": "Алгоритмические задачи", "order": 7, "description": "Поиск, фильтрация, подсчет частот и оптимизация"}
        )

        tasks_data = [
            {
                "number": 1,
                "title": "Привет, Мир!",
                "slug": "hello-world",
                "category": cat_basics,
                "difficulty": "easy",
                "xp_reward": 10,
                "description": (
                    "### Задание\n"
                    "Классическая первая задача программиста. Напишите программу, которая выводит в консоль строку `Hello, World!`.\n\n"
                    "Обратите внимание на точное совпадение регистра букв, запятой и восклицательного знака!"
                ),
                "input_format": "Входные данные отсутствуют.",
                "output_format": "Строка `Hello, World!`",
                "initial_code": "# Выведите приветствие в консоль\n",
                "hints": "Используйте встроенную функцию print('Hello, World!')",
                "reference_solution": "print('Hello, World!')",
                "tests": [
                    {"input": "", "output": "Hello, World!", "hidden": False},
                ]
            },
            {
                "number": 2,
                "title": "Сумма двух чисел",
                "slug": "sum-of-two-numbers",
                "category": cat_basics,
                "difficulty": "easy",
                "xp_reward": 15,
                "description": (
                    "### Задание\n"
                    "Программа получает на вход два целых числа (каждое на отдельной строке). "
                    "Вычислите их сумму и выведите полученный результат.\n\n"
                    "**Пример:**\n"
                    "Если на вход подано `5` и `7`, результатом должно быть `12`."
                ),
                "input_format": "Две строки: в первой строке число a, во второй — число b.",
                "output_format": "Одно целое число — сумма a + b.",
                "initial_code": "# Считайте два числа из стандартного ввода и выведите сумму\na = int(input())\nb = int(input())\n",
                "hints": "Функция input() возвращает строку. Для арифметических действий преобразуйте её в int(): a = int(input())",
                "reference_solution": "a = int(input())\nb = int(input())\nprint(a + b)",
                "tests": [
                    {"input": "5\n7\n", "output": "12", "hidden": False},
                    {"input": "100\n-25\n", "output": "75", "hidden": False},
                    {"input": "0\n0\n", "output": "0", "hidden": True},
                    {"input": "-150\n-50\n", "output": "-200", "hidden": True},
                ]
            },
            {
                "number": 3,
                "title": "Четное или нечетное",
                "slug": "even-or-odd",
                "category": cat_conditions,
                "difficulty": "easy",
                "xp_reward": 15,
                "description": (
                    "### Задание\n"
                    "Напишите программу, которая считывает целое число и проверяет его четность.\n"
                    "- Если число четное, выведите `EVEN`\n"
                    "- Если число нечетное, выведите `ODD`"
                ),
                "input_format": "Одно целое число n.",
                "output_format": "Строка EVEN или ODD.",
                "initial_code": "n = int(input())\n# Допишите проверку четности с помощью условия if/else\n",
                "hints": "Остаток от деления на 2 проверяется оператором %: if n % 2 == 0:",
                "reference_solution": "n = int(input())\nif n % 2 == 0:\n    print('EVEN')\nelse:\n    print('ODD')",
                "tests": [
                    {"input": "4\n", "output": "EVEN", "hidden": False},
                    {"input": "7\n", "output": "ODD", "hidden": False},
                    {"input": "0\n", "output": "EVEN", "hidden": True},
                    {"input": "-13\n", "output": "ODD", "hidden": True},
                    {"input": "1000002\n", "output": "EVEN", "hidden": True},
                ]
            },
            {
                "number": 4,
                "title": "Магия f-строк: Персональное приветствие",
                "slug": "f-strings-greeting",
                "category": cat_strings,
                "difficulty": "easy",
                "xp_reward": 20,
                "description": (
                    "### Задание (по материалам базы знаний NapkinContent)\n"
                    "В современном Python f-строки (`f'...'`) — это быстрый и удобный способ форматирования строк.\n\n"
                    "Программа получает на вход имя пользователя и его возраст (каждое значение на новой строке).\n"
                    "Выведите строку формата:\n"
                    "`Привет, <имя>! Через год тебе исполнится <возраст + 1>.`"
                ),
                "input_format": "Первая строка: имя (строка). Вторая строка: возраст (целое число).",
                "output_format": "Отформатированная f-строка.",
                "initial_code": "name = input().strip()\nage = int(input())\n# Используйте современную f-строку\n",
                "hints": "f'Привет, {name}! Через год тебе исполнится {age + 1}.'",
                "reference_solution": "name = input().strip()\nage = int(input())\nprint(f'Привет, {name}! Через год тебе исполнится {age + 1}.')",
                "tests": [
                    {"input": "Анна\n20\n", "output": "Привет, Анна! Через год тебе исполнится 21.", "hidden": False},
                    {"input": "Иван\n15\n", "output": "Привет, Иван! Через год тебе исполнится 16.", "hidden": False},
                    {"input": "Гвидо\n67\n", "output": "Привет, Гвидо! Через год тебе исполнится 68.", "hidden": True},
                ]
            },
            {
                "number": 5,
                "title": "Таблица умножения (Цикл for)",
                "slug": "multiplication-table",
                "category": cat_loops,
                "difficulty": "medium",
                "xp_reward": 25,
                "description": (
                    "### Задание\n"
                    "На вход подается число `n` (от 1 до 10). "
                    "Выведите таблицу умножения числа `n` на множители от 1 до 5 включительно в формате:\n"
                    "`n x i = res`"
                ),
                "input_format": "Одно целое число n.",
                "output_format": "5 строк с произведениями от 1 до 5.",
                "initial_code": "n = int(input())\nfor i in range(1, 6):\n    # Выведите строку таблицы\n    pass\n",
                "hints": "Используйте for i in range(1, 6): print(f'{n} x {i} = {n * i}')",
                "reference_solution": "n = int(input())\nfor i in range(1, 6):\n    print(f'{n} x {i} = {n * i}')",
                "tests": [
                    {"input": "3\n", "output": "3 x 1 = 3\n3 x 2 = 6\n3 x 3 = 9\n3 x 4 = 12\n3 x 5 = 15", "hidden": False},
                    {"input": "7\n", "output": "7 x 1 = 7\n7 x 2 = 14\n7 x 3 = 21\n7 x 4 = 28\n7 x 5 = 35", "hidden": False},
                    {"input": "10\n", "output": "10 x 1 = 10\n10 x 2 = 20\n10 x 3 = 30\n10 x 4 = 40\n10 x 5 = 50", "hidden": True},
                ]
            },
            {
                "number": 6,
                "title": "Фильтрация четных чисел в списке",
                "slug": "filter-even-numbers",
                "category": cat_lists,
                "difficulty": "medium",
                "xp_reward": 30,
                "description": (
                    "### Задание\n"
                    "На вход поступает строка чисел, разделенных пробелами. "
                    "Преобразуйте её в список чисел, отберите только четные числа, возведите каждое в квадрат и выведите их через пробел.\n\n"
                    "Если четных чисел нет, выведите пустую строку или `None` (ничего)."
                ),
                "input_format": "Строка из целых чисел через пробел.",
                "output_format": "Квадраты четных чисел через пробел.",
                "initial_code": "numbers = list(map(int, input().split()))\n# Отберите четные числа и выведите их квадраты через пробел\n",
                "hints": "Используйте списковое включение: [str(x**2) for x in numbers if x % 2 == 0] и ' '.join(...)",
                "reference_solution": "numbers = list(map(int, input().split()))\nres = [str(x**2) for x in numbers if x % 2 == 0]\nprint(' '.join(res))",
                "tests": [
                    {"input": "1 2 3 4 5 6\n", "output": "4 16 36", "hidden": False},
                    {"input": "7 9 11 13\n", "output": "", "hidden": False},
                    {"input": "-2 -4 0 10\n", "output": "4 16 0 100", "hidden": True},
                ]
            },
            {
                "number": 7,
                "title": "Палиндром ли строка?",
                "slug": "palindrome-check",
                "category": cat_strings,
                "difficulty": "easy",
                "xp_reward": 20,
                "description": (
                    "### Задание\n"
                    "Строка называется палиндромом, если она читается одинаково слева направо и справа налево. "
                    "На вход подается строка. Проверьте, является ли она палиндромом без учета регистра и пробелов.\n\n"
                    "Выведите `YES` или `NO`."
                ),
                "input_format": "Одна строка.",
                "output_format": "YES или NO.",
                "initial_code": "s = input()\n# Очистите строку от пробелов, приведите к нижнему регистру и сравните со срезом[::-1]\n",
                "hints": "s = s.replace(' ', '').lower(); print('YES' if s == s[::-1] else 'NO')",
                "reference_solution": "s = input().replace(' ', '').lower()\nif s == s[::-1]:\n    print('YES')\nelse:\n    print('NO')",
                "tests": [
                    {"input": "А роза упала на лапу Азора\n", "output": "YES", "hidden": False},
                    {"input": "racecar\n", "output": "YES", "hidden": False},
                    {"input": "Hello World\n", "output": "NO", "hidden": False},
                    {"input": "12321\n", "output": "YES", "hidden": True},
                    {"input": "python\n", "output": "NO", "hidden": True},
                ]
            },
            {
                "number": 8,
                "title": "Подсчет частоты слов (Группировка и Counter)",
                "slug": "word-frequency",
                "category": cat_algorithms,
                "difficulty": "hard",
                "xp_reward": 45,
                "description": (
                    "### Задание\n"
                    "Для подсчета частоты повторяющихся элементов в Python отлично подходят словари или `collections.Counter`.\n\n"
                    "На вход подается текст в одну строку. Подсчитайте частоту каждого слова (без учета регистра) и выведите слова в порядке убывания их частоты.\n"
                    "Если частоты равны, отсортируйте слова по алфавиту.\n"
                    "Формат вывода каждой строки: `<слово>: <количество>`."
                ),
                "input_format": "Одна строка с текстом, разделенным пробелами.",
                "output_format": "Список 'слово: количество' в каждой строке, отсортированный по правилам.",
                "initial_code": "text = input().lower().split()\n# Подсчитайте слова и отсортируйте по (-count, word)\n",
                "hints": "Используйте словарь count_map, а затем отсортируйте sorted(count_map.items(), key=lambda x: (-x[1], x[0]))",
                "reference_solution": (
                    "text = input().lower().split()\n"
                    "counts = {}\n"
                    "for w in text:\n"
                    "    counts[w] = counts.get(w, 0) + 1\n"
                    "sorted_words = sorted(counts.items(), key=lambda x: (-x[1], x[0]))\n"
                    "for word, count in sorted_words:\n"
                    "    print(f'{word}: {count}')"
                ),
                "tests": [
                    {
                        "input": "apple banana apple orange banana apple\n",
                        "output": "apple: 3\nbanana: 2\norange: 1",
                        "hidden": False
                    },
                    {
                        "input": "dog cat bird dog cat\n",
                        "output": "cat: 2\ndog: 2\nbird: 1",
                        "hidden": False
                    },
                    {
                        "input": "python python python django django fastapi\n",
                        "output": "python: 3\ndjango: 2\nfastapi: 1",
                        "hidden": True
                    }
                ]
            }
        ]

        for t_data in tasks_data:
            task, _ = Task.objects.update_or_create(
                slug=t_data["slug"],
                language=py_lang,
                defaults={
                    "number": t_data["number"],
                    "title": t_data["title"],
                    "category": t_data["category"],
                    "difficulty": t_data["difficulty"],
                    "xp_reward": t_data["xp_reward"],
                    "description": t_data["description"],
                    "input_format": t_data["input_format"],
                    "output_format": t_data["output_format"],
                    "initial_code": t_data["initial_code"],
                    "hints": t_data["hints"],
                    "reference_solution": t_data["reference_solution"],
                }
            )

            task.test_cases.all().delete()
            for idx, test_info in enumerate(t_data["tests"]):
                TestCase.objects.create(
                    task=task,
                    input_data=test_info["input"],
                    expected_output=test_info["output"],
                    is_hidden=test_info.get("hidden", False),
                    order=idx
                )
            self.stdout.write(f"Задача №{task.number} '{task.title}' инициализирована с {len(t_data['tests'])} тестами.")

        course, _ = Course.objects.update_or_create(
            slug="python-starter",
            language=py_lang,
            defaults={
                "title": "Python: Быстрый старт с нуля",
                "description": "Пошаговый интерактивный трек для начинающих: изучайте синтаксис, решайте задачи в тренажере и зарабатывайте XP!",
                "level": "novice",
                "estimated_time": "45 мин",
                "xp_total": 150,
                "order": 1,
                "is_published": True,
            }
        )

        mod1, _ = Module.objects.update_or_create(
            course=course,
            order=1,
            defaults={"title": "Модуль 1: Первые шаги в Python", "description": "Переменные, числа, строки и консольный ввод/вывод."}
        )

        task1 = Task.objects.filter(slug="hello-world").first()
        task2 = Task.objects.filter(slug="sum-of-two-numbers").first()
        task4 = Task.objects.filter(slug="f-strings-greeting").first()

        Lesson.objects.update_or_create(
            module=mod1,
            slug="lesson-hello",
            defaults={
                "title": "Урок 1: Функция print() и первая программа",
                "content": (
                    "Добро пожаловать в мир Python! 🚀\n\n"
                    "Для вывода информации на экран в Python используется встроенная функция `print()`.\n\n"
                    "```python\n"
                    "print('Привет, мир!')\n"
                    "```\n\n"
                    "Текст внутри круглых скобок должен быть заключен в одинарные или двойные кавычки. "
                    "Теперь перейдите к практическому тренажеру и напишите вашу первую строку кода!"
                ),
                "order": 1,
                "xp_reward": 15,
                "task": task1
            }
        )

        Lesson.objects.update_or_create(
            module=mod1,
            slug="lesson-input-vars",
            defaults={
                "title": "Урок 2: Ввод данных input() и переменные",
                "content": (
                    "Программа становится по-настоящему полезной, когда умеет работать с данными от пользователя.\n\n"
                    "Функция `input()` считывает строку из стандартного потока ввода:\n\n"
                    "```python\n"
                    "name = input()\n"
                    "print('Привет,', name)\n"
                    "```\n\n"
                    "По умолчанию `input()` возвращает строку (`str`). Если вам нужно число для сложения, оберните его в `int()`:\n\n"
                    "```python\n"
                    "num = int(input())\n"
                    "```"
                ),
                "order": 2,
                "xp_reward": 20,
                "task": task2
            }
        )

        Lesson.objects.update_or_create(
            module=mod1,
            slug="lesson-fstrings",
            defaults={
                "title": "Урок 3: Современные f-строки (f-strings)",
                "content": (
                    "f-строки появились в Python 3.6 и стали стандартом де-факто для форматирования строк.\n\n"
                    "Перед открывающей кавычкой ставится буква `f`, а внутри строки в фигурных скобках `{}` "
                    "можно указывать любые переменные или выражения:\n\n"
                    "```python\n"
                    "user = 'Алиса'\n"
                    "score = 42\n"
                    "print(f'Игрок {user} набрал {score * 2} очков!')\n"
                    "```\n\n"
                    "Это намного нагляднее и быстрее старых методов `%` и `.format()`."
                ),
                "order": 3,
                "xp_reward": 25,
                "task": task4
            }
        )

        self.stdout.write(self.style.SUCCESS("Данные успешно инициализированы!"))
