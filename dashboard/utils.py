"""Session cart + pricing helpers."""

from decimal import Decimal

from .models import Coupon, ProductVariant, SiteSettings

CART_KEY = 'rgs_cart'
COUPON_KEY = 'rgs_coupon'
ZERO = Decimal('0.00')


def money(value):
    return Decimal(value or 0).quantize(Decimal('0.01'))


class Cart:
    """A session-backed cart keyed by ProductVariant id."""

    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(CART_KEY)
        if not isinstance(cart, dict):
            cart = {}
            self.session[CART_KEY] = cart
        self.cart = cart
        self._rows = None

    # ------------------------------------------------------------- mutations
    def add(self, variant, quantity=1, replace=False):
        key = str(variant.id)
        current = int(self.cart.get(key, 0))
        new_qty = quantity if replace else current + quantity
        new_qty = max(1, min(int(new_qty), variant.quantity))
        self.cart[key] = new_qty
        self.save()
        return new_qty

    def set_quantity(self, variant_id, quantity):
        key = str(variant_id)
        if key not in self.cart:
            return
        quantity = int(quantity)
        if quantity <= 0:
            self.remove(variant_id)
            return
        variant = ProductVariant.objects.filter(id=variant_id).first()
        if variant:
            quantity = min(quantity, variant.quantity)
        self.cart[key] = max(1, quantity)
        self.save()

    def remove(self, variant_id):
        self.cart.pop(str(variant_id), None)
        self.save()

    def clear(self):
        self.session[CART_KEY] = {}
        self.cart = self.session[CART_KEY]
        self.session.pop(COUPON_KEY, None)
        self.save()

    def save(self):
        self.session[CART_KEY] = self.cart
        self.session.modified = True
        self._rows = None

    # ---------------------------------------------------------------- rows
    @property
    def rows(self):
        if self._rows is not None:
            return self._rows
        rows = []
        if not self.cart:
            self._rows = rows
            return rows
        ids = [int(k) for k in self.cart.keys() if str(k).isdigit()]
        variants = (
            ProductVariant.objects
            .filter(id__in=ids)
            .select_related('product', 'product__category', 'color', 'size')
            .prefetch_related('product__images', 'color__images')
        )
        stale = False
        for variant in variants:
            qty = int(self.cart.get(str(variant.id), 0))
            if qty <= 0 or not variant.product.is_active:
                stale = True
                self.cart.pop(str(variant.id), None)
                continue
            if qty > variant.quantity:
                qty = variant.quantity
                stale = True
                if qty <= 0:
                    self.cart.pop(str(variant.id), None)
                    continue
                self.cart[str(variant.id)] = qty
            unit = money(variant.product.final_price)
            rows.append({
                'variant': variant,
                'product': variant.product,
                'color': variant.color,
                'size': variant.size,
                'image': variant.image,
                'unit_price': unit,
                'quantity': qty,
                'line_total': money(unit * qty),
                'max_quantity': variant.quantity,
            })
        found_ids = {v.id for v in variants}
        for key in list(self.cart.keys()):
            if str(key).isdigit() and int(key) not in found_ids:
                self.cart.pop(key, None)
                stale = True
        if stale:
            self.save()
        self._rows = rows
        return rows

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return sum(row['quantity'] for row in self.rows)

    @property
    def count(self):
        return len(self)

    @property
    def is_empty(self):
        return not self.rows

    # ------------------------------------------------------------- pricing
    @property
    def subtotal(self):
        return money(sum((row['line_total'] for row in self.rows), ZERO))

    # ------------------------------------------------------------- coupons
    @property
    def coupon(self):
        code = self.session.get(COUPON_KEY)
        if not code:
            return None
        coupon = Coupon.objects.filter(code=code).first()
        if not coupon:
            self.session.pop(COUPON_KEY, None)
            return None
        ok, _ = coupon.validate_for(self.subtotal)
        if not ok:
            self.session.pop(COUPON_KEY, None)
            return None
        return coupon

    def set_coupon(self, code):
        self.session[COUPON_KEY] = code
        self.session.modified = True

    def clear_coupon(self):
        self.session.pop(COUPON_KEY, None)
        self.session.modified = True

    @property
    def coupon_discount(self):
        coupon = self.coupon
        if not coupon:
            return ZERO
        return money(coupon.amount_for(self.subtotal))

    def totals(self, country=None):
        settings_obj = SiteSettings.load()
        subtotal = self.subtotal
        discount = self.coupon_discount
        after_discount = max(ZERO, subtotal - discount)
        coupon = self.coupon
        free_coupon = bool(coupon and coupon.free_shipping)
        if free_coupon:
            shipping = ZERO
        else:
            shipping = money(settings_obj.shipping_for(after_discount, country))
        threshold = ZERO if free_coupon else settings_obj.free_threshold_for(country)
        return {
            'subtotal': subtotal,
            'discount': discount,
            'shipping': shipping,
            'total': money(after_discount + shipping),
            'coupon': coupon,
            'country': country,
            'settings': settings_obj,
            'free_shipping_threshold': threshold,
            'remaining_for_free': max(ZERO, threshold - after_discount),
        }

    def shipping_options(self, countries):
        """Shipping + total for each country — lets checkout update the summary live."""
        base = self.totals()
        after_discount = max(ZERO, base['subtotal'] - base['discount'])
        free_coupon = bool(base['coupon'] and base['coupon'].free_shipping)
        site = base['settings']
        options = []
        for country in countries:
            shipping = ZERO if free_coupon else money(site.shipping_for(after_discount, country))
            threshold = ZERO if free_coupon else site.free_threshold_for(country)
            options.append({
                'country': country,
                'shipping': shipping,
                'total': money(after_discount + shipping),
                'remaining_for_free': max(ZERO, threshold - after_discount) if threshold > ZERO else None,
            })
        return options
