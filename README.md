
# Тестовое задание Django/Backend
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

## Решение задач по "Построение системы для обучения"
### 1. Создание сущности продукта
Модель Course включает в себя поля для автора, названия, даты и времени старта, стоимости, а также поле указываюшее активен ли курс .
```
class Course(models.Model):
    """Модель продукта - курса."""

    author = models.CharField(
        max_length=250,
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    start_date = models.DateTimeField(
        auto_now=False,
        auto_now_add=False,
        verbose_name='Дата и время начала курса'
    )
    price = models.IntegerField(
        verbose_name='Цена',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно или нет',
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('-id',)

    def __str__(self):
        return self.title
```


### 2. Определение доступа через подписку
Модель Subscription

Моделька имеет три поля user (кто купил подписку), course (какой курс), created (тут подумал что пригодиться дата покупки чтобы если что нужно будет сделать подписку временной ).
    
```
    class Subscription(models.Model):
        """Модель подписки пользователя на курс."""
        course = models.ForeignKey(
            'courses.Course',
            on_delete=models.CASCADE,
            related_name='subscriptions',
            verbose_name='Курс'
        )
        user = models.ForeignKey(
            'users.CustomUser',
            on_delete=models.CASCADE,
            verbose_name='Пользователь',
            related_name='subscriptions'
        )
        created = models.DateTimeField(
            auto_now_add=True,
            verbose_name='Дата покупки'
        )
        class Meta:
            verbose_name = 'Подписка'
            verbose_name_plural = 'Подписки'
            ordering = ('-id',)


```
    
### 3. Создание сущности урока
Модель Lesson

Модель урока включает поля для названия и ссылки на видео. Урок связан с продуктом через ForeignKey.
 ```
    class Lesson(models.Model):
        """Модель урока."""
    
        title = models.CharField(
            max_length=250,
            verbose_name='Название',
        )
        link = models.URLField(
            max_length=250,
            verbose_name='Ссылка',
        )
        course = models.ForeignKey(
            'courses.Course',
            on_delete=models.CASCADE,
            related_name='lessons',
            verbose_name='Курс',
        )
    
        class Meta:
            verbose_name = 'Урок'
            verbose_name_plural = 'Уроки'
            ordering = ('id',)
    
        def __str__(self):
            return self.title
 
 ```

### 4. Создание сущности баланса пользователя
Модель Balance

Баланс имеет два поля user (владелец счета), amount (сколько бонусов). Для поля amount использовал PositiveIntegerField чтобы счет не был отрицательным также и указал default чтобы при создании она была ровна 1000. Также создал serializer для отображения баланса и возможности изменение баланса пользователя через REST-апи с правами is_staff=True у пользователя и подключил его в CustomUserSerializer. Баланс создается вместе с пользователем через signals
    
```
    class Balance(models.Model):
        """Модель баланса пользователя."""
        user = models.OneToOneField(
            'users.CustomUser',
            on_delete=models.CASCADE,
            verbose_name='Пользователь',
            related_name='balance'
        )
        amount = models.PositiveIntegerField(
            default=1000,
            verbose_name='бонус'
        )
    
        class Meta:
            verbose_name = 'Баланс'
            verbose_name_plural = 'Балансы'
            ordering = ('-id',)

    # Serializer

    
    class BalanceSerializer(serializers.ModelSerializer):
        
        class Meta:
            model = Balance
            fields = ('amount',)
    
    class CustomUserSerializer(UserSerializer):
        """Сериализатор пользователей."""
        balance = BalanceSerializer()
        class Meta:
            model = User
            fields = ('id', 'email', 'balance')

    # Signals

    @receiver(post_save, sender=CustomUser)
    def create_user_balance(sender, instance, created, **kwargs):
        if created:
            Balance.objects.create(user=instance)


```

## Решение задач по "Реализация базового сценария оплат"
### 1 Список доступных курсов
Задание было немного непонятным нужно было написать новый APIView или переделать существующий, но решил создать AccessCourseAPIView чтобы отображались только активные курсы и те которые еще не приобретены. Данные которые отображаются основные данные и количество уроков ( get_lessons_count() ).
```

    #  APIView
     def get_queryset(self):
        user = self.request.user
        
        if self.request.method in SAFE_METHODS:
            queryset = Course.objects.filter(is_active=True)
            
            if user.is_authenticated:
                queryset = queryset.exclude(subscriptions__user=user)
                
        else:
            queryset = Course.objects.all()
        return queryset

    # Serializer
    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return obj.lessons.count()

```

### 2 Покупка курса
Задекорированная функция pay() сперва проводит проверки.
1. проверка авторизован ли пользователь
2. проверка существует ли такой курс
3. проверка не подписан ли пользователь уже на этот курс
4. проверка достаточно ли средств для покупки

Затем используя транзакций снимают бонусы с баланса пользователя и создается подписка
```
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
```
### 3 Доступ к курсу 
Через permissions дается доступ ученикам и админу 

```
    # Permissions
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
```

### 4 Расприделение по группам
После создание курса через signals создаются 10 групп. После оформление подписки также через signals ученика добавляют в одну из 10 групп равномерно.
```
    
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
```


## Доп задание

Доп задание заставило помучеться пришлось некоторые места переписовать. Самое запутанное было вывести процент заполненности групп. Я вообще не понял как в примере вы получили 83 % если всего учеников 10. Может я чего-то не понимаю но у меня получалось 3.3 % и я решил что цифры выбраны рандомно и решил своем понимании задачу. 

```
    class CourseSerializer(serializers.ModelSerializer):
        """Список курсов."""

        lessons = MiniLessonSerializer(many=True, read_only=True)
        lessons_count = serializers.SerializerMethodField(read_only=True)
        students_count = serializers.SerializerMethodField(read_only=True)
        groups_filled_percent = serializers.SerializerMethodField(read_only=True)
        demand_course_percent = serializers.SerializerMethodField(read_only=True)

        def get_lessons_count(self, obj):
            """Количество уроков в курсе."""
            return obj.lessons.count()

        def get_students_count(self, obj):
            """Общее количество студентов на курсе."""
            return obj.subscriptions.count()
        
        def get_groups_filled_percent(self, obj):
            """Процент заполнения групп, если в группе максимум 30 чел.."""
            stu_count = obj.subscriptions.count()
            avg_stu_per = (stu_count / 10) * 100
            return round(avg_stu_per / 30, 2)
            

        def get_demand_course_percent(self, obj):
            """Процент приобретения курса."""
            students_count = obj.subscriptions.count()
            users_count = User.objects.count()
            return round((students_count*100) / users_count, 2)

        class Meta:
            model = Course
            fields = (
                'id',
                'author',
                'title',
                'start_date',
                'price',
                'lessons_count',
                'lessons',
                'demand_course_percent',
                'students_count',
                'groups_filled_percent',
            )
        
    class GroupSerializer(serializers.ModelSerializer):
        """Список групп."""

        course = serializers.StringRelatedField(read_only=True)
        students = StudentSerializer(many=True, read_only=True)

        class Meta:
            model = Group
            fields = (
                'title',
                'course',
                'students'
            )

```

### __Технологии__
* [Python 3.10.12](https://www.python.org/doc/)
* [Django 4.2.10](https://docs.djangoproject.com/en/4.2/)
* [Django REST Framework  3.14.0](https://www.django-rest-framework.org/)
* [Djoser  2.2.0](https://djoser.readthedocs.io/en/latest/getting_started.html)



