from gui.base import BaseManager, FormField
from PyQt6.QtCore import QDate
from typing import Any, cast
import db.functions as db
import uuid

from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QMessageBox,
)


class BookManager(BaseManager):
    def __init__(self):
        self.AUTHOR_COL = 2
        self.CATEGORY_COL = 3
        self.form_fields: list[FormField] = [
            (QLabel("Title"), QLineEdit(), True),
            (QLabel("Author"), self.create_author(), True),
            (QLabel("Category"), self.create_category(), True),
            (QLabel("ISBN Number"), self.create_isbn(), True),
            (QLabel("Release Date"), self.create_date_edit(), True),
            (QLabel("Description"), QTextEdit(), False),
        ]

        super().__init__(self.form_fields)

    def add_category(self, value: str):
        self.get_category().addItem(value)

    def delete_category(self, value: str):
        category = self.get_category()
        index = category.findText(value)
        category.removeItem(index)

    def edit_category(self, old_value: str, new_value: str):
        tm = self.get_table_model()
        category = self.get_category()
        index = category.findText(old_value)
        category.setItemText(index, new_value)
        # Change category name in table too
        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, self.CATEGORY_COL)) == old_value:
                tm.setData(tm.index(row, self.CATEGORY_COL), new_value)

    def get_category(self):
        return cast(QComboBox, self.form_fields[self.CATEGORY_COL][1])

    def add_author(self, value: str):
        self.get_author().addItem(value)

    def delete_author(self, value: str):
        author = self.get_author()
        index = author.findText(value)
        author.removeItem(index)

    def edit_author(self, old_value: str, new_value: str):
        tm = self.get_table_model()
        author = self.get_author()
        index = author.findText(old_value)
        author.setItemText(index, new_value)
        # Change author name in table too
        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, self.AUTHOR_COL)) == old_value:
                tm.setData(tm.index(row, self.AUTHOR_COL), new_value)

    def get_author(self):
        return cast(QComboBox, self.form_fields[self.AUTHOR_COL][1])

    def add_item(self) -> bool:
        row_data = self.extract_form_data()
        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        # This is to not the id field, cause we won't know id unless we add the item
        _, title, author, category, ISBN, release_date, description = row_data

        author_id = int(author.split(" ")[-1])
        category_id = int(category.split(" ")[-1])
        release_date = cast(
            db.sa.Date, QDate.fromString(release_date, "dd.MM.yyyy").toPyDate()
        )

        book = db.add_book(
            title=title,
            author_id=author_id,
            category_id=category_id,
            ISBN=ISBN,
            release_date=release_date,
            description=description,
        )

        if not book:
            QMessageBox.critical(
                self, "Error", "An error occurred while adding the book."
            )
            return False

        data: list[Any] = [
            book.id,
            *row_data[1:],
        ]

        self.insert_item_in_table(data)

        return super().add_item()

    def edit_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        book_id, title, author, category, ISBN, release_date, description = row_data

        book_id = int(book_id)
        author_id = int(author.split(" ")[-1])
        category_id = int(category.split(" ")[-1])
        release_date = cast(
            db.sa.Date, QDate.fromString(release_date, "dd.MM.yyyy").toPyDate()
        )
        description = row_data[6]

        book = db.edit_book(
            id=book_id,
            title=title,
            author_id=author_id,
            category_id=category_id,
            ISBN=ISBN,
            release_date=release_date,
            description=description,
        )

        if not book:
            QMessageBox.critical(
                self, "Error", "An error occurred while editing the book."
            )
            return False

        self.edit_item_in_table(row_data)

        return super().edit_item()

    def delete_item(self) -> None:
        tm = self.get_table_model()

        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
            book_id = tm.data(tm.index(row, 0))
            deleted = db.delete_book(int(book_id))
            print(book_id)

            if not deleted:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Error deleting this book. It is being used by a user.",
                )
                continue

            self.get_table_model().removeRow(row - deleted_count)
            deleted_count += 1

    def load_data(self) -> list[list[Any]]:
        books = db.get_books()
        data = []

        for book in books:
            data.append(
                [
                    book.id,
                    book.title,
                    f"{book.author.first_name} {book.author.last_name} {book.author.id}",
                    f"{book.category.name} {book.category.id}",
                    book.ISBN,
                    QDate.fromString(str(book.release_date), "yyyy-MM-dd").toString(
                        "dd.MM.yyyy"
                    ),
                    book.description,
                ]
            )

        return data

    def get_isbn(self):
        return cast(QLineEdit, self.form_fields[4][1])

    def create_date_edit(self) -> QDateEdit:
        date_edit = QDateEdit()
        date_edit.setDisplayFormat("dd.MM.yyyy")
        date_edit.setDate(QDate.currentDate())
        date_edit.setMaximumDate(QDate.currentDate())
        return date_edit

    def create_isbn(self) -> QLineEdit:
        isbn = QLineEdit()
        isbn.setText(uuid.uuid4().hex[:13].upper())
        isbn.setReadOnly(True)
        return isbn

    def create_author(self) -> QComboBox:
        author = QComboBox()
        authors = db.get_authors()
        author.addItems([f"{a.first_name} {a.last_name} {a.id}" for a in authors])
        return author

    def create_category(self) -> QComboBox:
        category = QComboBox()
        categories = db.get_categories()

        category.addItems([f"{c.name} {c.id}" for c in categories])
        return category
