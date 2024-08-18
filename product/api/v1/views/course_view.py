from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin,SAFE_METHODS
from api.v1.serializers.course_serializer import (AccessCourseSerializer, CourseSerializer,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer
from courses.models import Course
from users.models import Subscription


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.lessons.all()


class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.groups.all()


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """
    
    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer
    

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""
        user = self.request.user
        
        # Проверка авторизован ли пользователь
        if not user.is_authenticated:
            return Response(
                data={'error': 'Пользователь не аутентифицирован'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Проверка есть ли курс
        try:
            course = Course.objects.get(id=pk)
        except Course.DoesNotExist:
            return Response(
                data={'error':'Курс не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Проверка, подписан ли пользователь уже на курс
        if Subscription.objects.filter(course=course, user=user).exists():
            return Response(
                data={'error': 'Вы уже подписаны на этот курс'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # проверка достаточно ли средств для покупки
        if user.balance.amount < course.price:
            return Response(
                data={'error':'Недостаточно средств '}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Использование транзакций для обеспечения целостности данных
        with transaction.atomic():
            # Уменьшение баланса пользователя
            user.balance.amount -= course.price
            user.balance.save()
        
            # Создание подписки
            subscription = Subscription.objects.create(course=course, user=user)
    
        serializer = SubscriptionSerializer(subscription)

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )

class AccessCourseAPIView(generics.ListAPIView):
    
    serializer_class = AccessCourseSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if self.request.method in SAFE_METHODS:
            queryset = Course.objects.filter(is_active=True)
            
            if user.is_authenticated:
                queryset = queryset.exclude(subscriptions__user=user)
                
        else:
            queryset = Course.objects.all()
        return queryset