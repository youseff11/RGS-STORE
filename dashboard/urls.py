"""All routes for RGS TOWER — storefront + admin dashboard."""

from django.urls import path

from . import dashboard_views as dv
from . import views

urlpatterns = [
    # ------------------------------------------------------------ storefront
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('category/<str:slug>/', views.category_detail, name='category_detail'),
    path('product/<str:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('cart/coupon/apply/', views.coupon_apply, name='coupon_apply'),
    path('cart/coupon/remove/', views.coupon_remove, name='coupon_remove'),

    path('checkout/', views.checkout, name='checkout'),
    path('order/<str:number>/success/', views.order_success, name='order_success'),
    path('track/', views.track_order, name='track_order'),

    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ------------------------------------------------------------- dashboard
    path('dashboard/login/', dv.login_view, name='dash_login'),
    path('dashboard/logout/', dv.logout_view, name='dash_logout'),
    path('dashboard/', dv.index, name='dash_index'),

    # products
    path('dashboard/products/', dv.product_list, name='dash_products'),
    path('dashboard/products/new/', dv.product_form, name='dash_product_new'),
    path('dashboard/products/<int:pk>/edit/', dv.product_form, name='dash_product_edit'),
    path('dashboard/products/<int:pk>/delete/', dv.product_delete, name='dash_product_delete'),
    path('dashboard/products/<int:pk>/toggle/', dv.product_toggle, name='dash_product_toggle'),
    path('dashboard/products/<int:pk>/media/', dv.product_media, name='dash_product_media'),
    path('dashboard/products/<int:pk>/stock/', dv.product_stock, name='dash_product_stock'),
    path('dashboard/colors/<int:pk>/delete/', dv.color_delete, name='dash_color_delete'),
    path('dashboard/images/<int:pk>/delete/', dv.image_delete, name='dash_image_delete'),
    path('dashboard/images/<int:pk>/main/', dv.image_main, name='dash_image_main'),

    # categories
    path('dashboard/categories/', dv.category_list, name='dash_categories'),
    path('dashboard/categories/new/', dv.category_form, name='dash_category_new'),
    path('dashboard/categories/<int:pk>/edit/', dv.category_form, name='dash_category_edit'),
    path('dashboard/categories/<int:pk>/delete/', dv.category_delete, name='dash_category_delete'),

    # sizes
    path('dashboard/sizes/', dv.size_list, name='dash_sizes'),
    path('dashboard/sizes/<int:pk>/delete/', dv.size_delete, name='dash_size_delete'),

    # orders
    path('dashboard/orders/', dv.order_list, name='dash_orders'),
    path('dashboard/orders/<int:pk>/', dv.order_detail, name='dash_order_detail'),
    path('dashboard/orders/<int:pk>/status/', dv.order_status, name='dash_order_status'),
    path('dashboard/orders/<int:pk>/delete/', dv.order_delete, name='dash_order_delete'),
    path('dashboard/orders/<int:pk>/print/', dv.order_print, name='dash_order_print'),

    # coupons
    path('dashboard/coupons/', dv.coupon_list, name='dash_coupons'),
    path('dashboard/coupons/new/', dv.coupon_form, name='dash_coupon_new'),
    path('dashboard/coupons/<int:pk>/edit/', dv.coupon_form, name='dash_coupon_edit'),
    path('dashboard/coupons/<int:pk>/delete/', dv.coupon_delete, name='dash_coupon_delete'),

    # promotions
    path('dashboard/promotions/', dv.promotion_list, name='dash_promotions'),
    path('dashboard/promotions/new/', dv.promotion_form, name='dash_promotion_new'),
    path('dashboard/promotions/<int:pk>/edit/', dv.promotion_form, name='dash_promotion_edit'),
    path('dashboard/promotions/<int:pk>/delete/', dv.promotion_delete, name='dash_promotion_delete'),

    # announcements
    path('dashboard/announcements/', dv.announcement_list, name='dash_announcements'),
    path('dashboard/announcements/new/', dv.announcement_form, name='dash_announcement_new'),
    path('dashboard/announcements/<int:pk>/edit/', dv.announcement_form, name='dash_announcement_edit'),
    path('dashboard/announcements/<int:pk>/delete/', dv.announcement_delete, name='dash_announcement_delete'),

    # banners
    path('dashboard/banners/', dv.banner_list, name='dash_banners'),
    path('dashboard/banners/new/', dv.banner_form, name='dash_banner_new'),
    path('dashboard/banners/<int:pk>/edit/', dv.banner_form, name='dash_banner_edit'),
    path('dashboard/banners/<int:pk>/delete/', dv.banner_delete, name='dash_banner_delete'),

    # governorates
    path('dashboard/governorates/', dv.governorate_list, name='dash_governorates'),
    path('dashboard/governorates/new/', dv.governorate_form, name='dash_governorate_new'),
    path('dashboard/governorates/<int:pk>/edit/', dv.governorate_form, name='dash_governorate_edit'),
    path('dashboard/governorates/<int:pk>/delete/', dv.governorate_delete, name='dash_governorate_delete'),

    # messages
    path('dashboard/messages/', dv.message_list, name='dash_messages'),
    path('dashboard/messages/<int:pk>/', dv.message_detail, name='dash_message_detail'),
    path('dashboard/messages/<int:pk>/delete/', dv.message_delete, name='dash_message_delete'),

    # settings
    path('dashboard/settings/', dv.settings_view, name='dash_settings'),
]
