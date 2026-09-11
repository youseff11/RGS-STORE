"""Tiny bilingual layer (AR / EN) — no .po files needed."""

DEFAULT_LANG = 'en'


def current_lang():
    """The storefront is English-only — kept as a function so callers stay put."""
    return 'en'


def pick(ar, en):
    """Return the value matching the active language, falling back to the other."""
    if current_lang() == 'ar':
        return ar or en or ''
    return en or ar or ''


STRINGS = {
    # --- global / nav
    'brand': ('RGS TOWER', 'RGS TOWER'),
    'home': ('الرئيسية', 'Home'),
    'shop': ('المتجر', 'Shop'),
    'categories': ('الأقسام', 'Categories'),
    'new_arrivals': ('وصل حديثًا', 'New Arrivals'),
    'best_sellers': ('الأكثر مبيعًا', 'Best Sellers'),
    'sale': ('العروض', 'Sale'),
    'about': ('من نحن', 'About'),
    'contact': ('اتصل بنا', 'Contact'),
    'track_order': ('تتبع طلبك', 'Track Order'),
    'search': ('بحث', 'Search'),
    'search_placeholder': ('ابحث عن منتج...', 'Search for a product...'),
    'menu': ('القائمة', 'Menu'),
    'close': ('إغلاق', 'Close'),
    'language': ('اللغة', 'Language'),
    'theme': ('المظهر', 'Theme'),
    'dark_mode': ('الوضع الليلي', 'Dark mode'),
    'light_mode': ('الوضع النهاري', 'Light mode'),
    'all': ('الكل', 'All'),
    'view_all': ('عرض الكل', 'View all'),
    'back': ('رجوع', 'Back'),
    'save': ('حفظ', 'Save'),
    'cancel': ('إلغاء', 'Cancel'),
    'delete': ('حذف', 'Delete'),
    'edit': ('تعديل', 'Edit'),
    'add': ('إضافة', 'Add'),
    'actions': ('إجراءات', 'Actions'),
    'yes': ('نعم', 'Yes'),
    'no': ('لا', 'No'),
    'active': ('مفعّل', 'Active'),
    'inactive': ('غير مفعّل', 'Inactive'),
    'status': ('الحالة', 'Status'),
    'date': ('التاريخ', 'Date'),
    'none': ('لا يوجد', 'None'),
    'optional': ('اختياري', 'Optional'),
    'required_field': ('حقل مطلوب', 'Required'),
    'confirm_delete': ('متأكد من الحذف؟', 'Are you sure you want to delete this?'),

    # --- home / hero
    'hero_eyebrow': ('NEW SEASON', 'NEW SEASON'),
    'hero_line_1': ('WEAR YOUR', 'WEAR YOUR'),
    'hero_line_2': ('CONFIDENCE', 'CONFIDENCE'),
    'hero_tagline': ('خامات ممتازة. ستايلات مودرن. معمولة عشانك.',
                     'Premium quality. Modern styles. Made for you.'),
    'hero_cta': ('تسوّق الآن', 'SHOP NOW'),
    'hero_script': ('Better\nClothes\nBigger\nDreams', 'Better\nClothes\nBigger\nDreams'),
    'trust_delivery': ('توصيل سريع', 'Fast Delivery'),
    'trust_payment': ('دفع آمن', 'Secure Payment'),
    'trust_quality': ('جودة ممتازة', 'Premium Quality'),
    'hero_title': ('أناقة الرجل الحقيقي', 'Menswear, refined.'),
    'hero_sub': ('مجموعات مختارة بعناية — خامات فاخرة وتفاصيل تصنع الفرق',
                 'Carefully curated collections — premium fabrics, details that matter'),
    'shop_now': ('تسوّق الآن', 'Shop now'),
    'shop_collection': ('تسوّق المجموعة', 'Shop the collection'),
    'featured': ('منتجات مختارة', 'Featured'),
    'featured_sub': ('قطع اخترناها لك من أحدث المجموعات', 'Hand-picked pieces from our latest drops'),
    'browse_categories': ('تصفح الأقسام', 'Browse categories'),
    'categories_sub': ('اختار القسم اللي يناسب ستايلك', 'Pick the section that fits your style'),
    'new_sub': ('آخر ما وصل إلى المتجر', 'The latest to land in store'),
    'feature_delivery': ('توصيل لكل المحافظات', 'Delivery nationwide'),
    'feature_delivery_sub': ('شحن سريع وآمن لباب البيت', 'Fast and safe door-to-door shipping'),
    'feature_cod': ('الدفع عند الاستلام', 'Cash on delivery'),
    'feature_cod_sub': ('ادفع لما تستلم طلبك بالظبط', 'Pay only when your order arrives'),
    'feature_quality': ('خامات أصلية', 'Authentic quality'),
    'feature_quality_sub': ('نختار كل قطعة بعناية', 'Every piece is selected with care'),
    'feature_support': ('دعم على مدار اليوم', 'Support around the clock'),
    'feature_support_sub': ('فريقنا موجود للرد على أسئلتك', 'Our team is here to answer you'),

    # --- product
    'products': ('المنتجات', 'Products'),
    'product': ('المنتج', 'Product'),
    'price': ('السعر', 'Price'),
    'color': ('اللون', 'Color'),
    'colors': ('الألوان', 'Colors'),
    'size': ('المقاس', 'Size'),
    'sizes': ('المقاسات', 'Sizes'),
    'quantity': ('الكمية', 'Quantity'),
    'qty': ('الكمية', 'Qty'),
    'stock': ('المخزون', 'Stock'),
    'in_stock': ('متوفر', 'In stock'),
    'out_of_stock': ('نفد المخزون', 'Out of stock'),
    'only_left': ('باقي', 'Only'),
    'pieces_left': ('قطعة فقط', 'left'),
    'add_to_cart': ('أضف إلى السلة', 'Add to cart'),
    'buy_now': ('اشترِ الآن', 'Buy now'),
    'select_color': ('اختر اللون', 'Select a color'),
    'select_size': ('اختر المقاس', 'Select a size'),
    'choose_options': ('اختر اللون والمقاس أولاً', 'Choose a color and size first'),
    'description': ('الوصف', 'Description'),
    'details': ('التفاصيل', 'Details'),
    'shipping_info': ('الشحن والاستبدال', 'Shipping & returns'),
    'related_products': ('قد يعجبك أيضًا', 'You may also like'),
    'sku': ('كود المنتج', 'SKU'),
    'category': ('القسم', 'Category'),
    'new_badge': ('جديد', 'New'),
    'sale_badge': ('خصم', 'Sale'),
    'added_to_cart': ('تمت الإضافة إلى السلة', 'Added to your cart'),
    'no_products': ('لا توجد منتجات هنا حاليًا', 'No products here yet'),
    'no_products_sub': ('جرّب تغيير الفلاتر أو تصفح قسم آخر', 'Try changing the filters or browse another section'),

    # --- shop filters
    'filters': ('الفلاتر', 'Filters'),
    'sort_by': ('ترتيب حسب', 'Sort by'),
    'sort_newest': ('الأحدث', 'Newest'),
    'sort_price_low': ('السعر: من الأقل', 'Price: low to high'),
    'sort_price_high': ('السعر: من الأعلى', 'Price: high to low'),
    'sort_name': ('الاسم', 'Name'),
    'price_range': ('نطاق السعر', 'Price range'),
    'min_price': ('من', 'Min'),
    'max_price': ('إلى', 'Max'),
    'apply_filters': ('تطبيق', 'Apply'),
    'clear_filters': ('مسح الفلاتر', 'Clear filters'),
    'results_count': ('منتج', 'products'),
    'showing': ('عرض', 'Showing'),

    # --- cart
    'cart': ('سلة المشتريات', 'Shopping cart'),
    'cart_empty': ('سلتك فاضية', 'Your cart is empty'),
    'cart_empty_sub': ('ابدأ التسوق وضيف القطع اللي عجبتك', 'Start shopping and add the pieces you love'),
    'continue_shopping': ('متابعة التسوق', 'Continue shopping'),
    'order_summary': ('ملخص الطلب', 'Order summary'),
    'subtotal': ('الإجمالي الفرعي', 'Subtotal'),
    'discount': ('الخصم', 'Discount'),
    'shipping': ('الشحن', 'Shipping'),
    'free': ('مجاني', 'Free'),
    'total': ('الإجمالي', 'Total'),
    'promo_code': ('كود الخصم', 'Promo code'),
    'promo_placeholder': ('اكتب الكود هنا', 'Enter your code'),
    'apply': ('تطبيق', 'Apply'),
    'remove': ('حذف', 'Remove'),
    'checkout': ('إتمام الطلب', 'Checkout'),
    'update_cart': ('تحديث', 'Update'),
    'item_removed': ('تم حذف المنتج من السلة', 'Item removed from your cart'),
    'cart_updated': ('تم تحديث السلة', 'Cart updated'),
    'cart_cleared': ('تم تفريغ السلة', 'Cart cleared'),
    'free_shipping_left': ('اشترِ بـ {amount} كمان واحصل على شحن مجاني',
                           'Spend {amount} more for free shipping'),
    'free_shipping_earned': ('مبروك! حصلت على شحن مجاني', 'Nice! You unlocked free shipping'),

    # --- coupon messages
    'coupon_applied': ('تم تفعيل كود الخصم', 'Promo code applied'),
    'coupon_removed': ('تم إلغاء كود الخصم', 'Promo code removed'),
    'coupon_invalid': ('كود الخصم غير صحيح', 'Invalid promo code'),
    'coupon_inactive': ('كود الخصم غير مفعّل', 'This code is not active'),
    'coupon_not_started': ('كود الخصم لم يبدأ بعد', 'This code has not started yet'),
    'coupon_expired': ('انتهت صلاحية كود الخصم', 'This code has expired'),
    'coupon_used_up': ('تم استهلاك كود الخصم بالكامل', 'This code has reached its usage limit'),
    'coupon_min_order': ('الطلب أقل من الحد الأدنى لاستخدام الكود',
                         'Your order is below the minimum for this code'),

    # --- checkout
    'checkout_title': ('إتمام الطلب', 'Checkout'),
    'shipping_details': ('بيانات الشحن', 'Shipping details'),
    'full_name': ('الاسم بالكامل', 'Full name'),
    'phone': ('رقم الموبايل', 'Phone number'),
    'phone_alt': ('رقم موبايل آخر', 'Alternative phone'),
    'email': ('البريد الإلكتروني', 'Email'),
    'governorate': ('المحافظة', 'Governorate'),
    'city': ('المدينة / المنطقة', 'City / area'),
    'address': ('العنوان بالتفصيل', 'Full address'),
    'notes': ('ملاحظات على الطلب', 'Order notes'),
    'payment_method': ('طريقة الدفع', 'Payment method'),
    'cod': ('الدفع عند الاستلام', 'Cash on delivery'),
    'cod_note': ('هتدفع كاش للمندوب وقت ما تستلم طلبك',
                 'Pay the courier in cash when your order arrives'),
    'place_order': ('تأكيد الطلب', 'Place order'),
    'your_order': ('طلبك', 'Your order'),
    'order_received': ('تم استلام طلبك بنجاح', 'Your order has been received'),
    'order_received_sub': ('هنتواصل معاك في أقرب وقت لتأكيد الطلب',
                           'We will contact you shortly to confirm your order'),
    'order_number': ('رقم الطلب', 'Order number'),
    'save_order_number': ('احتفظ برقم الطلب لمتابعة حالته', 'Keep this number to track your order'),
    'orders_disabled': ('الطلبات متوقفة مؤقتًا، حاول لاحقًا', 'Orders are paused right now, please try later'),
    'checkout_empty': ('لا يمكن إتمام طلب بسلة فارغة', 'You cannot check out with an empty cart'),

    # --- tracking
    'track_title': ('تتبع طلبك', 'Track your order'),
    'track_sub': ('اكتب رقم الطلب ورقم الموبايل', 'Enter your order number and phone'),
    'track_button': ('تتبع', 'Track'),
    'track_not_found': ('لم نجد طلبًا بهذه البيانات', 'We could not find an order with these details'),
    'order_status': ('حالة الطلب', 'Order status'),
    'order_items': ('محتويات الطلب', 'Order items'),

    # --- contact
    'contact_title': ('تواصل معنا', 'Get in touch'),
    'contact_sub': ('أي استفسار؟ ابعتلنا وهنرد عليك بسرعة',
                    'Any question? Send us a message and we will reply shortly'),
    'your_name': ('اسمك', 'Your name'),
    'subject': ('الموضوع', 'Subject'),
    'message': ('الرسالة', 'Message'),
    'send_message': ('إرسال', 'Send'),
    'message_sent': ('وصلتنا رسالتك، شكرًا لتواصلك', 'Your message was sent, thank you'),

    # --- footer
    'quick_links': ('روابط سريعة', 'Quick links'),
    'help': ('المساعدة', 'Help'),
    'follow_us': ('تابعنا', 'Follow us'),
    'newsletter': ('النشرة البريدية', 'Newsletter'),
    'rights': ('كل الحقوق محفوظة', 'All rights reserved'),
    'cod_only': ('الدفع عند الاستلام فقط', 'Cash on delivery only'),

    # --- errors
    'not_found': ('الصفحة غير موجودة', 'Page not found'),
    'not_found_sub': ('الرابط اللي بتدور عليه مش موجود', 'The page you are looking for does not exist'),
    'go_home': ('الرجوع للرئيسية', 'Back home'),
    'server_error': ('حصل خطأ في الخادم', 'Something went wrong'),
}


def t(key, **kwargs):
    pair = STRINGS.get(key)
    if not pair:
        return key
    value = pair[0] if current_lang() == 'ar' else pair[1]
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value
