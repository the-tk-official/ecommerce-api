from datetime import datetime

import graphene
from django.conf import settings
from django.contrib.auth import authenticate
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload

from backend.authentication import TokenManager
from backend.permissions import is_authenticated, paginate
from .models import User, ImageUpload, UserProfile, UserAddress


class UserType(DjangoObjectType):
    """Response with user data"""
    class Meta:
        model = User


class ImageUploadType(DjangoObjectType):
    """Response with image data"""
    image = graphene.String()

    class Meta:
        model = ImageUpload

    def resolve_image(self, info):
        if self.image:
            return "{}{}{}".format(settings.S3_BUCKET_URL, settings.MEDIA_URL, self.image)
        return ""


class UserProfileType(DjangoObjectType):
    """Response with profile data"""
    class Meta:
        model = UserProfile


class UserAddressType(DjangoObjectType):
    """Response with address data"""
    class Meta:
        model = UserAddress


class RegisterUser(graphene.Mutation):
    """User Registration"""
    status = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)

    def mutate(self, info, email, password, **kwargs):
        User.objects.create_user(email=email, password=password, **kwargs)

        return RegisterUser(status=True, message="User created successfully")


class LoginUser(graphene.Mutation):
    """Login User"""
    access = graphene.String(required=True)
    refresh = graphene.String(required=True)
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = authenticate(username=email, password=password)

        if not user:
            raise Exception('Invalid credentials')

        user.last_login = datetime.now()
        user.save()

        access = TokenManager.get_access_token({'user_id': str(user.id)})
        refresh = TokenManager.get_refresh_token({'user_id': str(user.id)})

        return LoginUser(access=access, refresh=refresh, user=user)


class GetAccess(graphene.Mutation):
    """Get Access Token from Refresh Token"""
    access = graphene.String()

    class Arguments:
        refresh = graphene.String(required=True)

    def mutate(self, info, refresh):
        token = TokenManager.decode_token(refresh)

        if not token or token['token_type'] != 'refresh':
            raise Exception('Invalid token or has expired')

        access = TokenManager.get_access_token({'user_id': token['user_id']})

        return GetAccess(access=access)


class ImageUploadMain(graphene.Mutation):
    """Uploading a image"""
    image = graphene.Field(ImageUploadType)

    class Arguments:
        image = Upload(required=True)

    def mutate(self, info, image):
        image = ImageUpload.objects.create(image=image)

        return ImageUploadMain(image=image)


class UserProfileInput(graphene.InputObjectType):
    profile_picture = graphene.String()
    country_code = graphene.String()


class CreateUserProfile(graphene.Mutation):
    """Creating the user profile"""
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput()
        dob = graphene.Date(required=True)
        gender = graphene.String(required=True)
        phone_number = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, profile_data, **kwargs):
        user_profile = UserProfile.objects.create(
            user_id=info.context.user.id,
            **profile_data, **kwargs
        )

        return CreateUserProfile(user_profile = user_profile)


class UpdateUserProfile(graphene.Mutation):
    """Updating the user profile"""
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput()
        dob = graphene.Date()
        gender = graphene.String()
        phone_number = graphene.String()

    @is_authenticated
    def mutate(self, info, profile_data, **kwargs):
        try:
            info.context.user.user_profile
        except Exception:
            raise Exception("You don't have profile to Update")

        UserProfile.objects.filter(user_id=info.context.user.id).update(**profile_data, **kwargs)

        return UpdateUserProfile(user_profile=info.context.user.user_profile)


class AddressInput(graphene.InputObjectType):
    country = graphene.String()
    city = graphene.String()
    street = graphene.String()


class CreateUserAddress(graphene.Mutation):
    """Creating a user address"""
    address = graphene.Field(UserAddressType)

    class Arguments:
        address_data = AddressInput(required=True)
        is_default = graphene.Boolean()

    @is_authenticated
    def mutate(self, info, address_data, is_default=False):
        try:
            user_profile_id = info.context.user.user_profile.id
        except Exception:
            raise Exception('You need a profile to create an address')

        existing_addresses = UserAddress.objects.filter(user_profile_id=user_profile_id)

        if is_default:
            existing_addresses.update(is_default=False)

        address = UserAddress.objects.create(
            user_profile_id=user_profile_id,
            **address_data,
            is_default=is_default
        )

        return CreateUserAddress(address=address)


class UpdateUserAddress(graphene.Mutation):
    """Updating a user address"""
    address = graphene.Field(UserAddressType)

    class Argument:
        address_data = AddressInput()
        is_default = graphene.Boolean()
        address_id = graphene.UUID(required=True)

    @is_authenticated
    def mutate(self, info, address_data, address_id, is_default=False):
        profile_id = info.context.user.user_profile.id

        address = UserAddress.objects.filter(
            user_profile_id=profile_id,
            id=address_id
        ).update(is_default=is_default, **address_data)

        if is_default:
            UserAddress.objects.filter(user_profile_id=profile_id).update(id=address_id).update(is_default=False)

        return UpdateUserAddress(
            address=UserAddress.objects.get(id=address_id)
        )


class DeleteUserAddress(graphene.Mutation):
    """Deleting a user address"""
    status = graphene.Boolean()

    class Arguments:
        address_id = graphene.UUID(required=True)

    @is_authenticated
    def mutate(self, info, address_id):
        profile_id = info.context.user.user_profile.id
        UserAddress.objects.filter(
            user_profile_id=profile_id,
            id=address_id
        ).delete()

        return DeleteUserAddress(status=True)


class Query(graphene.ObjectType):
    users = graphene.Field(
        paginate(UserType),
        page=graphene.Int(),
        is_active=graphene.Boolean(),
        is_staff=graphene.Boolean(),
        description='Response data in pagination about existing users'
    )
    images = graphene.Field(
        paginate(ImageUploadType), page=graphene.Int(),
        description='Response data in pagination about existing images'
    )
    me = graphene.Field(UserType, description='Response data about the authorized user')

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(**kwargs)

    def resolve_images(self, info, **kwargs):
        return ImageUpload.objects.filter(**kwargs)

    @is_authenticated
    def resolve_me(self, info):
        return info.context.user


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    login_user = LoginUser.Field()
    get_access = GetAccess.Field()
    image_upload = ImageUploadMain.Field()
    create_user_profile = CreateUserProfile.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_user_address = CreateUserAddress.Field()
    update_user_address = UpdateUserAddress.Field()
    delete_user_address = DeleteUserAddress.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
