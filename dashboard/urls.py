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
    path('order/<str:number>/pay/', views.order_pay, name='order_pay'),
    path('order/<str:number>/pay/paypal/create/', views.paypal_create, name='paypal_create'),
    path('order/<str:number>/pay/paypal/capture/', views.paypal_capture, name='paypal_capture'),
    path('order/<str:number>/pay/sent/', views.order_paid_manual, name='order_paid_manual'),
    path('track/', views.track_order, name='track_order'),

    # accounts
    path('account/', views.account, name='account'),
    path('account/login/', views.account_login, name='account_login'),
    path('account/register/', views.account_register, name='account_register'),
    path('account/logout/', views.account_logout, name='account_logout'),
    path('account/orders/<str:number>/', views.account_order, name='account_order'),

    # portfolio + reviews + pages
    path('works/', views.works, name='works'),
    path('works/<str:slug>/', views.work_detail, name='work_detail'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/new/', views.review_submit, name='review_submit'),
    path('policies/<str:slug>/', views.policy_detail, name='policy_detail'),
    path('lang/<str:code>/', views.set_language, name='set_language'),

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

    # customers
    path('dashboard/customers/', dv.customer_list, name='dash_customers'),
    path('dashboard/customers/export/', dv.customer_export, name='dash_customers_export'),
    path('dashboard/customers/<int:pk>/', dv.customer_detail, name='dash_customer_detail'),
    path('dashboard/customers/<int:pk>/toggle/', dv.customer_toggle, name='dash_customer_toggle'),
    path('dashboard/customers/<int:pk>/delete/', dv.customer_delete, name='dash_customer_delete'),

    # orders — payment
    path('dashboard/orders/<int:pk>/payment/', dv.order_payment, name='dash_order_payment'),

    # portfolio
    path('dashboard/works/', dv.work_list, name='dash_works'),
    path('dashboard/works/new/', dv.work_form, name='dash_work_new'),
    path('dashboard/works/<int:pk>/edit/', dv.work_form, name='dash_work_edit'),
    path('dashboard/works/<int:pk>/media/', dv.work_media, name='dash_work_media'),
    path('dashboard/works/<int:pk>/toggle/<str:field>/', dv.work_toggle, name='dash_work_toggle'),
    path('dashboard/works/<int:pk>/delete/', dv.work_delete, name='dash_work_delete'),
    path('dashboard/works/media/<int:pk>/delete/', dv.work_media_delete, name='dash_work_media_delete'),
    path('dashboard/works/media/<int:pk>/cover/', dv.work_media_cover, name='dash_work_media_cover'),
    path('dashboard/works/categories/', dv.work_category_list, name='dash_work_categories'),
    path('dashboard/works/categories/<int:pk>/delete/', dv.work_category_delete, name='dash_work_category_delete'),

    # reviews
    path('dashboard/reviews/', dv.review_list, name='dash_reviews'),
    path('dashboard/reviews/<int:pk>/', dv.review_edit, name='dash_review_edit'),
    path('dashboard/reviews/<int:pk>/toggle/<str:field>/', dv.review_toggle, name='dash_review_toggle'),
    path('dashboard/reviews/<int:pk>/delete/', dv.review_delete, name='dash_review_delete'),

    # homepage + navbar + policies
    path('dashboard/homepage/', dv.home_sections, name='dash_home'),
    path('dashboard/homepage/<int:pk>/', dv.home_section_edit, name='dash_home_edit'),
    path('dashboard/homepage/<int:pk>/move/<str:direction>/', dv.home_section_move, name='dash_home_move'),
    path('dashboard/homepage/<int:pk>/toggle/', dv.home_section_toggle, name='dash_home_toggle'),
    path('dashboard/navbar/', dv.nav_list, name='dash_nav'),
    path('dashboard/navbar/new/', dv.nav_form, name='dash_nav_new'),
    path('dashboard/navbar/<int:pk>/edit/', dv.nav_form, name='dash_nav_edit'),
    path('dashboard/navbar/<int:pk>/move/<str:direction>/', dv.nav_move, name='dash_nav_move'),
    path('dashboard/navbar/<int:pk>/toggle/', dv.nav_toggle, name='dash_nav_toggle'),
    path('dashboard/navbar/<int:pk>/delete/', dv.nav_delete, name='dash_nav_delete'),
    path('dashboard/policies/', dv.policy_list, name='dash_policies'),
    path('dashboard/policies/new/', dv.policy_form, name='dash_policy_new'),
    path('dashboard/policies/<int:pk>/edit/', dv.policy_form, name='dash_policy_edit'),
    path('dashboard/policies/<int:pk>/delete/', dv.policy_delete, name='dash_policy_delete'),

    # staff
    path('dashboard/staff/', dv.staff_list, name='dash_staff'),
    path('dashboard/staff/new/', dv.staff_form, name='dash_staff_new'),
    path('dashboard/staff/<int:pk>/edit/', dv.staff_form, name='dash_staff_edit'),
    path('dashboard/staff/<int:pk>/delete/', dv.staff_delete, name='dash_staff_delete'),

    # settings
    path('dashboard/settings/', dv.settings_view, name='dash_settings'),
    path('dashboard/settings/payments/', dv.payment_settings, name='dash_payments'),
]
