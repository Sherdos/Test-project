from django.contrib import admin

from courses.models import Course, Lesson, Group

# Register your models here.


admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Group)
