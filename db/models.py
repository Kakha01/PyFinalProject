import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declarative_base,
    relationship,
)

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    author_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("authors.id"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey("categories.id"), nullable=False
    )
    ISBN: Mapped[str] = mapped_column(sa.String, nullable=False, unique=True)
    release_date: Mapped[sa.Date] = mapped_column(sa.Date, nullable=False)
    description: Mapped[str] = mapped_column(sa.String)

    author: Mapped["Author"] = relationship("Author", back_populates="books")
    category: Mapped["Category"] = relationship("Category", back_populates="books")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(sa.String)

    books: Mapped[list["Book"]] = relationship(
        "Book", order_by=Book.id, back_populates="category"
    )


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    last_name: Mapped[str] = mapped_column(sa.String, nullable=False)
    bio: Mapped[str] = mapped_column(sa.String)

    books: Mapped[list["Book"]] = relationship(
        "Book", order_by=Book.id, back_populates="author"
    )
