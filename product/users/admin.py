from django.contrib import admin
from users.models import Subscription,CustomUser,Balance
# Register your models here.


admin.site.register(Subscription)
admin.site.register(CustomUser)
admin.site.register(Balance)