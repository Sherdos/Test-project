from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import Subscription, Balance

User = get_user_model()


class BalanceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Balance
        fields = ('amount',)

class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователей."""
    balance = BalanceSerializer()
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'balance')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""
    course = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('user','course')

