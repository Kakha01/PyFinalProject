import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, joinedload
from typing import Optional
from db.models import Base, Book, Category, Author
import logging

db = sa.create_engine("sqlite:///data.db")
Session = sessionmaker(bind=db)


def create_all() -> None:
    Base.metadata.create_all(db)
    logging.info("Database tables created")


def add_category(name: str, description: Optional[str]) -> int:
    with Session() as s:
        try:
            category = Category(name=name, description=description)
            s.add(category)
            s.commit()
            logging.info(f"Category added: {name} (ID: {category.id})")
            return category.id
        except Exception:
            return -1


def delete_category(id: int) -> bool:
    with Session() as s:
        try:
            category = s.query(Category).filter_by(id=id).first()
            s.delete(category)
            s.commit()
            logging.info(f"Category deleted: ID {id}")
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
            logging.info(f"Category edited: {name} (ID: {id})")
            return True
        except Exception:
            return False


def get_category(id: int) -> Category | None:
    with Session() as s:
        return s.query(Category).filter_by(id=id).first()


def get_categories() -> list[Category]:
    with Session() as s:
        return s.query(Category).options(joinedload(Category.books)).all()


def add_author(first_name: str, last_name: str, bio: Optional[str]) -> int:
    with Session() as s:
        try:
            author = Author(first_name=first_name, last_name=last_name, bio=bio)
            s.add(author)
            s.commit()
            logging.info(f"Author added: {first_name} {last_name} (ID: {author.id})")
            return author.id
        except Exception:
            return -1


def delete_author(id: int) -> bool:
    with Session() as s:
        try:
            author = s.query(Author).filter_by(id=id).first()
            s.delete(author)
            s.commit()
            logging.info(f"Author deleted: ID {id}")
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
            logging.info(f"Author edited: {first_name} {last_name} (ID: {id})")
            return True
        except Exception:
            return False


def get_author(id: int) -> Author | None:
    with Session() as s:
        return s.query(Author).filter_by(id=id).first()


def get_authors() -> list[Author]:
    with Session() as s:
        return s.query(Author).options(joinedload(Author.books)).all()


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
            logging.info(f"Book added: {title} (ID: {book.id})")

            book = (
                s.query(Book)
                .options(joinedload(Book.author), joinedload(Book.category))
                .filter_by(id=book.id)
                .first()
            )

            return book
        except Exception:
            return None


def delete_book(id: int) -> bool:
    with Session() as s:
        try:
            book = s.query(Book).filter_by(id=id).first()
            s.delete(book)
            s.commit()
            logging.info(f"Book deleted: ID {id}")
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
            logging.info(f"Book edited: {title} (ID: {id})")
            return True
        except Exception:
            return False


def get_book(id: int) -> Book | None:
    with Session() as s:
        return (
            s.query(Book)
            .options(joinedload(Book.author), joinedload(Book.category))
            .filter_by(id=id)
            .first()
        )


def get_books() -> list[Book]:
    with Session() as s:
        return (
            s.query(Book)
            .options(joinedload(Book.author), joinedload(Book.category))
            .all()
        )
