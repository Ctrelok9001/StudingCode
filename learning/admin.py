from django.contrib import admin
from .models import Language, Category, Task, TestCase, Submission, Course, Module, Lesson, LessonProgress, UserProfile


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'language', 'category', 'difficulty', 'xp_reward')
    list_filter = ('language', 'difficulty', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
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
