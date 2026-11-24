from django.contrib import admin
from .models import (
    Language, Category, Task, TestCase, Submission, Course, Module,
    Lesson, LessonProgress, UserProfile, TaskHintUnlock, Tag,
    QuizQuestion, QuizOption, UserQuizAttempt, CourseCertificate
)


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'language', 'category', 'difficulty', 'xp_reward')
    list_filter = ('language', 'difficulty', 'category', 'tags')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    inlines = [TestCaseInline]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'order')
    list_filter = ('language',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'status', 'tests_passed', 'tests_total', 'execution_time_ms', 'created_at')
    list_filter = ('status', 'task__language')
    search_fields = ('user__username', 'task__title')


@admin.register(TaskHintUnlock)
class TaskHintUnlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'created_at')
    list_filter = ('task',)
    search_fields = ('user__username', 'task__title')


class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 4


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'lesson', 'order', 'xp_reward')
    list_filter = ('lesson__module__course',)
    search_fields = ('question', 'explanation')
    inlines = [QuizOptionInline]


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_code', 'user', 'course', 'issued_at')
    list_filter = ('course',)
    search_fields = ('certificate_code', 'user__username', 'course__title')


@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'is_passed', 'created_at')
    list_filter = ('is_passed',)
    search_fields = ('user__username',)


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'level', 'estimated_time', 'xp_total', 'is_published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    inlines = [LessonInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'xp', 'streak_days', 'last_activity_date', 'level')
    search_fields = ('user__username',)
