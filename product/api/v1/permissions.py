from rest_framework.permissions import BasePermission, SAFE_METHODS
from courses.models import Course
from users.models import Subscription


def make_payment(request):
    # TODO
    pass


class IsStudentOrIsAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            course_id = view.kwargs.get('course_id')
            course = Course.objects.get(id=course_id)
            return request.user.is_staff or request.user in course.students.all()
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user in obj.course.students.all() or request.user.is_staff
        return request.user.is_staff

class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
