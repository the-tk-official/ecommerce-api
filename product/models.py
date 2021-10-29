from django.db import models

from user.models import ImageUpload, User


class Category(models.Model):
    """Class for creation a category table in a database"""
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Business(models.Model):
    """Class for creation a business table in a database"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_business')
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Businesses'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Class for creation a product table in a database"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product_categories')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_product')
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_available = models.PositiveIntegerField()
    total_count = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", )
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.name}    |    {self.business.name}"


class ProductImage(models.Model):
    """Class for creation a product image table in a database"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ForeignKey(ImageUpload, on_delete=models.CASCADE, related_name='image_product')
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"{self.product.name}    |    {self.is_cover}"


class ProductComment(models.Model):
    """Class for creation a product comment in a database"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comments')
    comment = models.TextField()
    rate = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Product Comments'

    def __str__(self):
        return f"{self.product.name}    |    {self.user.first_name}"


class Wish(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_wish')
    products = models.ManyToManyField(Product, related_name='products_wished')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Wishes'


class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_cart')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_cart')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name}    |    {self.user.first_name}"

    class Meta:
        ordering = ('-created_at', )


class RequestCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_request')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_request')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_request')
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', )
