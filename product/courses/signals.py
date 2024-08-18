from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from users.models import Subscription
from courses.models import Group, Course
from django.contrib.auth import get_user_model


@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """
    Распределение нового студента в группу курса.

    """
    if created:
        all_groups = instance.course.groups.all()
        
        # Нахождение группы с наименьшим числом студентов
        group = min(all_groups, key=lambda x: x.students.count())
        
        group.students.add(instance.user)
        



@receiver(post_save, sender=Course)
def post_save_course(sender, instance: Course, created, **kwargs):
    """
    Создание групп для курса.

    """

    if created:
        for i in range(1,11):
            title = f'Группа №{i} Курс - {instance.title}'
            Group.objects.create(course=instance, title=title)