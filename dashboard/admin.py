"""Django admin registration (backup to the custom dashboard)."""

from django.contrib import admin

from .models import (
    Announcement, Banner, Category, ContactMessage, Coupon, CustomerProfile, Governorate,
    HomeSection, NavLink, Order, OrderItem, Policy, Product, ProductColor, ProductImage,
    ProductVariant, Promotion, Review, SiteSettings, Size, StaffProfile, Work, WorkCategory,
    WorkMedia,
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
    list_display = ('order_number', 'full_name', 'phone', 'total', 'payment_method',
                    'payment_status', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('order_number', 'full_name', 'phone')
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'used_count', 'is_active')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'scope', 'discount_type', 'value', 'is_active')


class WorkMediaInline(admin.TabularInline):
    model = WorkMedia
    extra = 0


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('title_ar', 'category', 'is_active', 'is_featured', 'ordering')
    list_filter = ('is_active', 'is_featured', 'category')
    inlines = [WorkMediaInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('is_approved', 'is_featured', 'rating')
    search_fields = ('name', 'comment')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'governorate', 'city', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')


admin.site.register([
    Announcement, Banner, Size, Governorate, SiteSettings, ContactMessage,
    WorkCategory, HomeSection, NavLink, Policy, StaffProfile,
])

admin.site.site_header = 'RGS TOWER'
admin.site.site_title = 'RGS TOWER'
admin.site.index_title = 'إدارة المتجر'
