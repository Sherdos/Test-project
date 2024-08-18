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
            
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return False
            
            has_subscription = Subscription.objects.filter(user=request.user, course=course).exists()
            return request.user.is_staff or has_subscription
        
        return request.user.is_staff

    def has_object_permission(self, request, view, obj):
        
        if request.method in SAFE_METHODS:
            has_subscription = Subscription.objects.filter(user=request.user, course=obj.course).exists()
            
            return request.user.is_staff or has_subscription
        
        return request.user.is_staff

class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
