from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify  # <--- Импортируем slugify

# Пайдаланыушылар
class User(AbstractUser):
    ROLES = (('admin', 'Admin'), ('client', 'Client'))
    role = models.CharField(max_length=10, choices=ROLES, default='client')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

# Категориялар
class Category(models.Model):
    name = models.CharField(max_length=100)
    # blank=True разрешает создавать категорию без ручного ввода слага
    slug = models.SlugField(unique=True, blank=True) 
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self): return self.name

    # АВТОМАТИЧЕСКАЯ ГЕНЕРАЦИЯ СЛАГА
    def save(self, *args, **kwargs):
        if not self.slug:  # Если слаг не передан
            self.slug = slugify(self.name)  # Создаем его из имени (Smartfon -> smartfon)
        super().save(*args, **kwargs)

# Продуктлар
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(blank=True) # Тоже можно сделать автоматическим
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self): return self.name

    # Тоже добавим авто-слаг для продуктов, чтобы было удобно
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# Корзина
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

# Корзинага косылган онын 1 элементы
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

# Заказлар
class Order(models.Model):
    STATUS_CHOICES = (('pending', 'Kútilmekte'), ('paid', 'Tólendi'), ('shipped', 'Jiberildi'), ('canceled', 'Biykar etildi'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

#Заказлардын 1 элементы
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

# Отзывлар
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)