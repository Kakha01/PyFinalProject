from PyQt6.QtWidgets import QLabel, QLineEdit, QTextEdit, QMessageBox
from gui.base import BaseManager, FormField
from PyQt6.QtCore import pyqtSignal
import db.functions as db
from typing import Any


class AuthorManager(BaseManager):
    authorAdd = pyqtSignal(str)
    authorDelete = pyqtSignal(str)
    authorEdit = pyqtSignal(str, str)

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
                "label": QLabel("First Name"),
                "input": QLineEdit(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Last Name"),
                "input": QLineEdit(),
                "required": True,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Bio"),
                "input": QTextEdit(),
                "required": False,
                "hidden_col": False,
                "hidden_field": False,
            },
            {
                "label": QLabel("Books"),
                "input": QLineEdit(),
                "required": False,
                "hidden_col": False,
                "hidden_field": True,
            },
        ]

        super().__init__(self.form_fields)

    def add_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            return False

        _, first_name, last_name, bio, _ = row_data

        author_id = db.add_author(first_name, last_name, bio)

        if author_id == -1:
            return False

        self.authorAdd.emit(f"{first_name} {last_name} {author_id}")

        self.insert_item_in_table([author_id, first_name, last_name, bio, 0])

        return super().add_item()

    def delete_item(self):
        tm = self.get_table_model()
        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
            row = row - deleted_count

            author_id = tm.data(tm.index(row, 0))
            author_name = tm.data(tm.index(row, 1))
            author_last_name = tm.data(tm.index(row, 2))

            deleted = db.delete_author(int(author_id))

            if not deleted:
                QMessageBox.critical(
                    self, "Error", "Cannot delete author. It is being used by a book."
                )
                continue

            self.authorDelete.emit(f"{author_name} {author_last_name} {author_id}")
            self.get_table_model().removeRow(row)
            deleted_count += 1

    def edit_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        author_id, first_name, last_name, bio, _ = row_data

        old_author = db.get_author(int(author_id))

        if not old_author:
            QMessageBox.critical(
                self, "Error", "An error occurred while getting old author."
            )
            return False

        author = db.edit_author(int(author_id), first_name, last_name, bio)

        if not author:
            QMessageBox.critical(
                self, "Error", "An error occurred while editing the author."
            )
            return False

        self.authorEdit.emit(
            f"{old_author.first_name} {old_author.last_name} {old_author.id}",
            f"{first_name} {last_name} {author_id}",
        )

        self.edit_item_in_table(row_data)

        return super().edit_item()

    def load_data(self) -> list[list[Any]]:
        authors = db.get_authors()
        data = []

        for author in authors:
            data.append(
                [
                    author.id,
                    author.first_name,
                    author.last_name,
                    author.bio,
                    len(author.books),
                ]
            )

        return data

    def increment_author_books(self, author_id: str) -> None:
        tm = self.get_table_model()

        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, 0)) == author_id:
                count = int(tm.data(tm.index(row, 4)))
                tm.setData(tm.index(row, 4), count + 1)
                break

    def decrement_author_books(self, author_id: str) -> None:
        tm = self.get_table_model()

        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, 0)) == author_id:
                count = int(tm.data(tm.index(row, 4)))
                tm.setData(tm.index(row, 4), count - 1)
                break
