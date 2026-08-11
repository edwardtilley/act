from django.db import models
from django.conf import settings


class Product(models.Model):
    CATEGORY_CERTIFICATION = 'certification'
    CATEGORY_CANDIDATE = 'candidate'
    CATEGORY_MEMBERSHIP = 'membership'
    CATEGORIES = [
        (CATEGORY_CERTIFICATION, 'Certification Training'),
        (CATEGORY_CANDIDATE, 'Candidate / Parliament'),
        (CATEGORY_MEMBERSHIP, 'Membership'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField()
    category = models.CharField(max_length=30, choices=CATEGORIES, default=CATEGORY_MEMBERSHIP)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    @property
    def price_display(self):
        return f'${self.price_cents / 100:,.2f}'

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_cents(self):
        return sum(item.subtotal_cents for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_display(self):
        return f'${self.total_cents / 100:,.2f}'

    def __str__(self):
        return f'Cart #{self.pk} ({self.user.username})'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('cart', 'product')]

    @property
    def subtotal_cents(self):
        return self.product.price_cents * self.quantity

    @property
    def subtotal_display(self):
        return f'${self.subtotal_cents / 100:,.2f}'

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CANCELLED = 'cancelled'
    STATUSES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='shop_orders')
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    total_cents = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def total_display(self):
        return f'${self.total_cents / 100:,.2f}'

    def __str__(self):
        return f'Order #{self.pk} ({self.user.username}, {self.status})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def subtotal_cents(self):
        return self.price_cents * self.quantity

    def __str__(self):
        return f'{self.quantity} x {self.name}'


class Payment(models.Model):
    GATEWAY_HUB = 'hub'
    GATEWAY_TEST = 'test'
    GATEWAYS = [
        (GATEWAY_HUB, 'Hub Payment Gateway'),
        (GATEWAY_TEST, 'Test Gateway'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUSES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    gateway = models.CharField(max_length=20, choices=GATEWAYS)
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    amount_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def amount_display(self):
        return f'${self.amount_cents / 100:,.2f}'

    def __str__(self):
        return f'Payment #{self.pk} ({self.gateway}, {self.status})'


class ApiKey(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_SYSOP = 'sysop'
    ROLES = [
        (ROLE_ADMIN, 'Admin (full access)'),
        (ROLE_SYSOP, 'SysOp (read-only)'),
    ]

    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=64, unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default=ROLE_SYSOP)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.role})'