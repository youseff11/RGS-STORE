"""Django admin registration (backup to the custom dashboard)."""

from django.contrib import admin

from .models import (
    Announcement, Banner, Category, ContactMessage, Coupon, Governorate, Order,
    OrderItem, Product, ProductColor, ProductImage, ProductVariant, Promotion,
    SiteSettings, Size,
)


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'category', 'price', 'total_stock', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'is_new', 'category')
    search_fields = ('name_ar', 'name_en', 'sku')
    inlines = [ProductColorInline, ProductImageInline, ProductVariantInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'is_active', 'ordering')
    list_editable = ('is_active', 'ordering')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'phone', 'total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone')
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'used_count', 'is_active')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'scope', 'discount_type', 'value', 'is_active')


admin.site.register([Announcement, Banner, Size, Governorate, SiteSettings, ContactMessage])

admin.site.site_header = 'RGS TOWER'
admin.site.site_title = 'RGS TOWER'
admin.site.index_title = 'إدارة المتجر'
