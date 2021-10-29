import uuid

from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    """Manager for working with user creation"""
    def create_user(self, email, password, **extra_fields):
        """Creating a user"""
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Creating a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('first_name', 'admin')
        extra_fields.setdefault('last_name', 'admin')

        if not extra_fields.get('is_staff', False):
            raise ValueError('Superuser must have is_staff=True.')

        if not extra_fields.get('is_superuser', False):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Class for creation a user table in a database"""
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    class Meta:
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.email}    |    {self.created_at}'

    def save(self, *args, **kwargs):
        """Undo a save implementation"""
        super().clean_fields()
        super(User, self).save(*args, **kwargs)


class ImageUpload(models.Model):
    image = models.ImageField(upload_to="images/%Y/%m/%d/")

    class Meta:
        verbose_name_plural = 'Images'

    def __str__(self):
        return str(self.image)


class UserProfile(models.Model):
    """Class for creation a user profile table in a database"""

    GENDERS_CHOICES = (
        (None, 'Choose your gender'),
        ('Male', 'Male'),
        ('Female', 'Female')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    profile_picture = models.ForeignKey(ImageUpload, null=True, on_delete=models.SET_NULL, related_name='user_images')
    dob = models.DateField()
    gender = models.CharField(max_length=8, choices=GENDERS_CHOICES, blank=True, null=True)
    country_code = models.CharField(default='+998', max_length=8, editable=False)
    phone_regex = RegexValidator(regex=r'd{2}\s\d{3}\s\d{2}\s\d{2}',
                                 message='Phone number must be entered in the format: "** *** ** **".'
                                         'Up to the 9 digits allowed.')
    phone_number = models.CharField(validators=[phone_regex], max_length=16, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)

    class Meta:
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.user.email


class UserAddress(models.Model):
    """Class for creation a user address table in a database"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_addresses')
    country = models.CharField(max_length=128, default="Uzbekistan")
    city = models.CharField(max_length=128, default="Tashkent")
    street = models.TextField(max_length=128, default="Yunus Abad")
    is_default = models.BooleanField(default=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, unique=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return self.user_profile.user.email
