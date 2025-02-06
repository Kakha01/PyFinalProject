import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    sessionmaker,
    declarative_base,
    relationship,
    joinedload,
)
from typing import Optional

db = sa.create_engine("sqlite:///management.db")
Session = sessionmaker(bind=db)
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


def create_all() -> None:
    Base.metadata.create_all(db)


def add_category(name: str, description: Optional[str]) -> int:
    with Session() as s:
        try:
            category = Category(name=name, description=description)
            s.add(category)
            s.commit()
            return category.id
        except Exception:
            return -1


def delete_category(id: int) -> bool:
    with Session() as s:
        try:
            category = s.query(Category).filter_by(id=id).first()
            s.delete(category)
            s.commit()
            return True
        except Exception:
            return False


def edit_category(id: int, name: str, description: Optional[str]) -> bool:
    with Session() as s:
        try:
            category = s.query(Category).filter_by(id=id).first()

            if not category:
                return False

            category.name = name

            if description:
                category.description = description

            s.commit()
            return True
        except Exception:
            return False


def get_category(id: int) -> Category | None:
    with Session() as s:
        return s.query(Category).filter_by(id=id).first()


def get_categories() -> list[Category]:
    with Session() as s:
        return s.query(Category).all()


def add_author(first_name: str, last_name: str, bio: Optional[str]) -> int:
    with Session() as s:
        try:
            author = Author(first_name=first_name, last_name=last_name, bio=bio)
            s.add(author)
            s.commit()
            return author.id
        except Exception:
            return -1


def delete_author(id: int) -> bool:
    with Session() as s:
        try:
            author = s.query(Author).filter_by(id=id).first()
            s.delete(author)
            s.commit()
            return True
        except Exception:
            return False


def edit_author(id: int, first_name: str, last_name: str, bio: Optional[str]) -> bool:
    with Session() as s:
        try:
            author = s.query(Author).filter_by(id=id).first()

            if not author:
                return False

            author.first_name = first_name
            author.last_name = last_name

            if bio:
                author.bio = bio

            s.commit()
            return True
        except Exception:
            return False


def get_author(id: int) -> Author | None:
    with Session() as s:
        return s.query(Author).filter_by(id=id).first()


def get_authors() -> list[Author]:
    with Session() as s:
        return s.query(Author).all()


def add_book(
    title: str,
    author_id: int,
    category_id: int,
    ISBN: str,
    release_date: sa.Date,
    description: Optional[str],
) -> Book | None:
    with Session() as s:
        try:
            book = Book(
                title=title,
                author_id=author_id,
                category_id=category_id,
                ISBN=ISBN,
                release_date=release_date,
                description=description,
            )
            s.add(book)
            s.commit()
            s.refresh(book)

            book = (
                s.query(Book)
                .options(joinedload(Book.author), joinedload(Book.category))
                .filter_by(id=book.id)
                .first()
            )

            print(book)

            return book
        except Exception:
            return None


def delete_book(id: int) -> bool:
    with Session() as s:
        try:
            book = s.query(Book).filter_by(id=id).first()
            s.delete(book)
            s.commit()
            return True
        except Exception:
            return False


def edit_book(
    id: int,
    title: str,
    author_id: int,
    category_id: int,
    ISBN: str,
    release_date: sa.Date,
    description: Optional[str],
) -> bool:
    with Session() as s:
        try:
            book = s.query(Book).filter_by(id=id).first()

            if not book:
                return False

            book.title = title
            book.author_id = author_id
            book.category_id = category_id
            book.ISBN = ISBN
            book.release_date = release_date

            if description:
                book.description = description

            s.commit()
            return True
        except Exception:
            return False


def get_books() -> list[Book]:
    with Session() as s:
        return (
            s.query(Book)
            .options(joinedload(Book.author), joinedload(Book.category))
            .all()
        )
