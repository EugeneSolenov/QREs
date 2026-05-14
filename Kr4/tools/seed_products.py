import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402


arr = [
    {
        "title": "Notebook",
        "price": Decimal("1299.90"),
        "count": 5,
        "description": "Portable work notebook",
    },
    {
        "title": "Keyboard",
        "price": Decimal("99.50"),
        "count": 12,
        "description": "Compact mechanical keyboard",
    },
]


def main():
    with SessionLocal() as ses:
        for x in arr:
            old = ses.scalar(select(Product).where(Product.title == x["title"]))
            if old is None:
                ses.add(Product(**x))

        ses.commit()

        for p in ses.scalars(select(Product).order_by(Product.id)):
            print(
                f"{p.id}: {p.title}, "
                f"price={p.price}, count={p.count}, "
                f"description={p.description}"
            )


if __name__ == "__main__":
    main()
