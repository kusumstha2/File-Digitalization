from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.core.validators import MinLengthValidator, RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)  # Ensure user is active
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)  # Ensure email is unique
    password = models.CharField(max_length=300, validators=[MinLengthValidator(8)])
    username = models.CharField(max_length=300, null=True, blank=True)
    phone = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$')])
    role = models.ForeignKey(Group, related_name='user_groups', on_delete=models.CASCADE, default=3)
    is_active = models.BooleanField(default=True)
  
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True
    )

    USERNAME_FIELD = 'email'  # Login with email
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


