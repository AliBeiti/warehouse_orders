from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product  # change 'core' if your app name is different


class Command(BaseCommand):
    help = "Create Master Best Kalıcı Oje (MBKO) products automatically."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=int,
            default=169,
            help="Starting number (e.g. 169)",
        )
        parser.add_argument(
            "--end",
            type=int,
            default=214,
            help="Ending number (inclusive, e.g. 214)",
        )

    def handle(self, *args, **options):
        start_num = options["start"]
        end_num = options["end"]

        # *** CONFIG ***
        NAME_PREFIX = "Master Best Non Stick Builder Gel 50Ml"
        CODE_PREFIX = "MBNSB"

        USE_LEADING_ZEROS = True  # True -> 001, 002; False -> 1, 2, 3
        IMAGE_PREFIX = "NB"          # if files are '169.jpg', '170.jpg', leave empty

        BASE_PRICE = 504.00          # set to Decimal("5.90") if you want a price
        UNIT = "adet"                  # e.g. "15ml"
        CATEGORY = None            # set to a Category instance if you want

        # Get existing MBKO codes so we don’t create duplicates
        existing_codes = set(
            Product.objects.filter(code__startswith=CODE_PREFIX)
            .values_list("code", flat=True)
        )

        products = []

        for i in range(start_num, end_num + 1):
            if USE_LEADING_ZEROS:
                num_str = f"{i:02d}"
            else:
                num_str = str(i)

            name = f"{NAME_PREFIX} {num_str}"
            code = f"{CODE_PREFIX}{num_str}"

            # Image path inside MEDIA_ROOT
            if IMAGE_PREFIX:
                image_path = f"products/{IMAGE_PREFIX}{num_str}.jpg"
            else:
                image_path = f"products/{num_str}.jpg"

            if code in existing_codes:
                self.stdout.write(f"Skipping existing product with code {code}")
                continue

            pick_order = 361+i
            display_order = i

            p = Product(
                category=CATEGORY,
                name=name,
                code=code,
                pick_order=pick_order,
                display_order=display_order,
                price=BASE_PRICE,
                discount_percent=0,
                discount_price=None,
                unit=UNIT,
                is_active=True,
                image=image_path,
            )
            products.append(p)

        if not products:
            self.stdout.write(self.style.WARNING("No new products to create."))
            return

        with transaction.atomic():
            Product.objects.bulk_create(products)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(products)} products from {start_num} to {end_num}."
            )
        )
