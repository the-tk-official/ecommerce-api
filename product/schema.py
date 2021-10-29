import graphene

from django.db.models import Q
from graphene_django import DjangoObjectType

from .models import (
    Category, Business, Product, ProductComment,
    ProductImage, Wish, Cart, RequestCart
)
from backend.permissions import get_query, paginate, is_authenticated


class CategoryType(DjangoObjectType):

    class Meta:
        model = Category


class BusinessType(DjangoObjectType):

    class Meta:
        model = Business


class ProductType(DjangoObjectType):

    class Meta:
        model = Product


class ProductCommentType(DjangoObjectType):

    class Meta:
        model = ProductComment


class ProductImageType(DjangoObjectType):

    class Meta:
        model = ProductImage


class WishType(DjangoObjectType):

    class Meta:
        model = Wish


class CartType(DjangoObjectType):

    class Meta:
        model = Cart


class RequestCartType(DjangoObjectType):

    class Meta:
        model = RequestCart


class Query(graphene.ObjectType):
    categories = graphene.List(
        CategoryType,
        name=graphene.String(),
        description='Response data about existing categories'
    )
    products = graphene.Field(
        paginate(ProductType), search=graphene.String(),
        min_price=graphene.Decimal(), max_price=graphene.Float(),
        category=graphene.String(), business=graphene.String(),
        sort_by=graphene.String(), is_asc=graphene.Boolean(),
        description='Response data paginated about existing products'
    )
    product = graphene.Field(
        ProductType, id=graphene.ID(required=True),
        description='Response data about existing product'
    )
    carts = graphene.List(
        CartType, name=graphene.String(),
        description='Response data about existing products in user cart'
    )
    request_carts = graphene.List(
        RequestCartType, name=graphene.String(),
        description='Response data about existing products in payment cart'
    )

    def resolve_categories(self, info, name):
        query = Category.objects.prefetch_related('product_categories')

        if name:
            query = query.filter(Q(name__icontains=name) | Q(name__iexact=name)).distinct()

        return query

    @is_authenticated
    def resolve_carts(self, info, name=False):
        query = Cart.objects.select_related("user", "product").filter(user_id=info.context.user.id)

        if name:
            query = query.filter(Q(product__name__icontains=name) | Q(product__name__iexact=name)).distinct()

        return query

    @is_authenticated
    def resolve_request_carts(self, info, name=False):
        query = RequestCart.objects.select_related(
            "user", "product", "business").filter(business__user_id=info.context.user.id)

        if name:
            query = query.filter(Q(product__name__icontains=name) | Q(product__name__iexact=name)).distinct()

        return query

    def resolve_products(self, info, **kwargs):
        query = Product.objects.select_related('category', 'business').prefetch_related(
            'product_images', 'product_comments', 'products_wished', 'product_cart', 'product_request'
        )

        if kwargs.get('search', None):
            qs = kwargs['search']
            search_fields = (
                'name', 'description', 'category__name'
            )
            search_data = get_query(qs, search_fields)
            query = query.filter(search_data)

        if kwargs.get('min_price', None):
            qs = kwargs['min_price']

            query.filter(Q(price__qt=qs) | Q(price=qs)).distinct()

        if kwargs.get('max_price', None):
            qs = kwargs['max_price']

            query.filter(Q(price__lt=qs) | Q(price=qs)).distinct()

        if kwargs.get('category', None):
            qs = kwargs['category']

            query.filter(Q(product__name__icontains=qs) | Q(category__name__iexct=qs)).distinct()

        if kwargs.get('business', None):
            qs = kwargs['business']

            query.filter(Q(bussiness__name__icontains=qs) | Q(bussiness__name__iexct=qs)).distinct()

        if kwargs.get('sort_by', None):
            qs = kwargs['sort_by']

            is_asc = kwargs.get('is_asc', False)

            if not is_asc:
                qs = f'-{qs}'

            query = query.order_by(qs)

        return query

    def resolve_product(self, info, id):
        query = Product.objects.select_related('category', 'business').prefetch_related(
            'product_images', 'product_comments', 'products_wished', 'product_cart', 'product_request'
        ).get(id=id)

        return query


class CreateBusiness(graphene.Mutation):
    """Create a business card"""
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        business = Business.objects.create(name=name, user_id=info.context.user.id)

        return CreateBusiness(business=business)


class UpdateBusiness(graphene.Mutation):
    """Update a business card"""
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        try:
            instanse = info.context.user.user_business
        except Exception:
            raise Exception("You doesn't have a business to update")

        instanse.name = name
        instanse.save()

        return UpdateBusiness(business=instanse)


class DeleteBusiness(graphene.Mutation):
    """Delete a business card"""
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        Business.objects.filter(user_id=info.context.user.id).delete()

        return DeleteBusiness(
            status=True
        )


class ProductInput(graphene.InputObjectType):
    name = graphene.String()
    price = graphene.Decimal()
    description = graphene.String()
    category_id = graphene.ID()


class ProductImageInput(graphene.InputObjectType):
    image_id = graphene.ID(required=True)
    is_cover = graphene.Boolean


class CreateProduct(graphene.Mutation):
    """Create a product"""
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput(required=True)
        total_count = graphene.Int(required=True)
        images = graphene.List(ProductImageInput)

    @is_authenticated
    def mutate(self, info, product_data, images, **kwargs):
        try:
            business_id = info.context.user.user_business.id
        except Exception:
            raise Exception("User doesn't have a business card")

        existing_product = Product.objects.filter(business_id=business_id, name=product_data['name'])

        if existing_product:
            raise Exception("You already have a product with this name")

        product_data['total_available'] = product_data['total_count']

        product = Product.objects.create(**product_data, **kwargs)

        ProductImage.objects.bulk_create([
            ProductImage(product_id=product.id, **image) for image in images
        ])

        return CreateProduct(
            product=product
        )


class UpdateProduct(graphene.Mutation):
    """Update a product"""
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput()
        total_available = graphene.Int(required=True)
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_data, product_id, **kwargs):
        try:
            business_id = info.context.user.user_business.id
        except Exception:
            raise Exception("User doesn't have a business card")

        if product_data.get('name', None):
            existing_product = Product.objects.filter(business_id=business_id, name=product_data['name'])
            if existing_product:
                raise Exception("You already have a product with this name")

        Product.objects.filter(id=product_id, business_id=business_id).update(**product_data, **kwargs)
        
        return UpdateProduct(product=Product.objects.get(id=product_id))


class DeleteProduct(graphene.Mutation):
    """Update a product"""
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_id):
        Product.objects.filter(id=product_id, business_id=info.context.user.user_business.id).delete()

        return DeleteProduct(status=True)


class UpdateProductImage(graphene.Mutation):
    """Update a product image"""
    image = graphene.Field(ProductImageType)

    class Arguments:
        image_data = ProductImageInput()
        id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, image_data, id):
        try:
            business_id = info.context.user.user_business.id
        except Exception:
            raise Exception("You don't have a business card, access denied")

        image = ProductImage.objects.filter(id=id, product__business_id=business_id)

        if not image:
            raise Exception("You don't own this product")
        
        image.update(**image_data)

        if image_data.get('is_cover', False):
            ProductImage.objects.filter(product__business_id=business_id).exclude(id=id).update(is_cover=False)

        return UpdateProductImage(
            image = ProductImage.objects.get(id=id)
        )


class CreateProductComment(graphene.Mutation):
    """Create a product comment"""
    product_comment = graphene.Field(ProductCommentType)

    class Arguments:
        product_id = graphene.ID(required=True)
        comment = graphene.String(required=True)
        rate = graphene.Int()

    @is_authenticated
    def mutate(self, info, product_id, **kwargs):
        user_business_id = None
        try:
            user_business_id = info.context.user.user_business.id
        except Exception:
            pass

        if user_business_id:
            own_product = Product.objects.filter(business_id=user_business_id, id=product_id)
            if own_product:
                raise Exception("You can't commit on you product")

        ProductComment.objects.filter(user=info.context.user.id, product_id=product_id).delete()

        product_comment = ProductComment.objects.create(product_id=product_id, **kwargs)

        return CreateProductComment(product_comment=product_comment)


class WishList(graphene.Mutation):
    """Add or remove an item from wish list by clicking on icon"""
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)
        is_check = graphene.Boolean()

    @is_authenticated
    def mutate(self, info, product_id, is_check=False):
        try:
            product = Product.objects.get(id=product_id)
        except Exception:
            raise Exception("Product with product_id doesn't exist")

        try:
            user_wish = info.context.user.user_wish
        except Exception:
            user_wish = Wish.objects.create(user_id=info.context.user.id)

        product_exists = user_wish.products.filter(id=product_id)

        if product_exists:
            if is_check:
                return WishList(status=True)
            user_wish.products.remove(product)
        else:
            if is_check:
                return WishList(status=False)
            user_wish.products.add()

        return WishList(status=True)


class CreateCartItem(graphene.Mutation):
    """Add a product in cart"""
    cart_item = graphene.Field(CartType)

    class Arguments:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int()

    @is_authenticated
    def mutate(self, info, product_id, **kwargs):
        Cart.objects.filter(product_id=product_id, user_id=info.context.user.id).delete()

        cart_item = Cart.objects.create(product_id=product_id, user_id=info.context.user.id, **kwargs)

        return CreateCartItem(
            cart_item=cart_item
        )


class UpdateCartItem(graphene.Mutation):
    """Update a product data from cart"""
    cart_item = graphene.Field(CartType)

    class Arguments:
        cart_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    @is_authenticated
    def mutate(self, info, cart_id, **kwargs):
        Cart.objects.filter(id=cart_id, user_id=info.context.user.id).update(**kwargs)

        return UpdateCartItem(
            cart_item=Cart.objects.get(id=cart_id)
        )


class DeleteCartItem(graphene.Mutation):
    """Delete a product from cart"""
    status = graphene.Boolean()

    class Arguments:
        cart_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, cart_id):
        Cart.objects.filter(id=cart_id, user_id=info.context.user.id).delete()

        return DeleteCartItem(
            status=True
        )


class CompletePayment(graphene.Mutation):
    """Create a payment cart"""
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        user_carts = Cart.objects.filter(user_id=info.context.user.id)

        RequestCart.objects.bulk_create([
            RequestCart(
                user_id=info.context.user.id,
                business_id=cart_item.product.business.id,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                price=cart_item.quantity * cart_item.product.price
            ) for cart_item in user_carts
        ])

        user_carts.delete()

        return CompletePayment(
            status=True
        )


class Mutation(graphene.ObjectType):
    create_business = CreateBusiness.Field()
    update_business = UpdateBusiness.Field()
    delete_business = DeleteBusiness.Field()
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    update_product_image = UpdateProductImage.Field()
    create_product_comment = CreateProductComment.Field()
    handle_wish_list = WishList.Field()
    create_cart_item = CreateCartItem.Field()
    update_cart_item = UpdateCartItem.Field()
    delete_cart_item = DeleteCartItem.Field()
    complete_payment = CompletePayment.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
