from gui.base import BaseManager, FormField
from PyQt6.QtCore import QDate, pyqtSignal
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
    incrementCategoryBooks = pyqtSignal(str)
    decrementCategoryBooks = pyqtSignal(str)

    incrementAuthorBooks = pyqtSignal(str)
    decrementAuthorBooks = pyqtSignal(str)

    def __init__(self):
        self.form_fields: list[FormField] = [
            {
                "label": QLabel("ID"),
                "input": QLineEdit(),
                "required": False,
                "hidden_col": True,
                "hidden_field": True,
            },
            {
                "label": QLabel("Title"),
                "input": QLineEdit(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Author"),
                "input": self.create_author(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Category"),
                "input": self.create_category(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("ISBN Number"),
                "input": self.create_isbn(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Release Date"),
                "input": self.create_date_edit(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Description"),
                "input": QTextEdit(),
                "required": False,
                "hidden_col": False,
                "hidden_field": False,
            },
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
            if tm.data(tm.index(row, 3)) == old_value:
                tm.setData(tm.index(row, 3), new_value)

    def get_category(self) -> QComboBox:
        return cast(QComboBox, self.form_fields[3]["input"])

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
            if tm.data(tm.index(row, 2)) == old_value:
                tm.setData(tm.index(row, 2), new_value)

    def get_author(self) -> QComboBox:
        return cast(QComboBox, self.form_fields[2]["input"])

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
        self.incrementCategoryBooks.emit(str(category_id))
        self.incrementAuthorBooks.emit(str(author_id))

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

        old_book = db.get_book(book_id)

        if not old_book:
            QMessageBox.critical(
                self, "Error", "An error occurred while editing the book."
            )
            return False

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

        if old_book.category_id != category_id:
            self.decrementCategoryBooks.emit(str(old_book.category_id))
            self.incrementCategoryBooks.emit(str(category_id))

        if old_book.author_id != author_id:
            self.decrementAuthorBooks.emit(str(old_book.author_id))
            self.incrementAuthorBooks.emit(str(author_id))

        self.edit_item_in_table(row_data)

        return super().edit_item()

    def delete_item(self) -> None:
        tm = self.get_table_model()

        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
            row = row - deleted_count
            book_id = tm.data(tm.index(row, 0))
            deleted = db.delete_book(int(book_id))
            author_id = cast(str, tm.data(tm.index(row, 2))).split(" ")[-1]
            category_id = cast(str, tm.data(tm.index(row, 3))).split(" ")[-1]

            if not deleted:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Error deleting this book. It is being used by a user.",
                )
                continue

            self.get_table_model().removeRow(row)
            self.decrementCategoryBooks.emit(category_id)
            self.decrementAuthorBooks.emit(author_id)
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
