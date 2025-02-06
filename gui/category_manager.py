from PyQt6.QtWidgets import QLabel, QLineEdit, QTextEdit, QMessageBox
from gui.base import BaseManager, FormField
from PyQt6.QtCore import pyqtSignal
import db.functions as db
from typing import Any


class CategoryManager(BaseManager):
    categoryAdd = pyqtSignal(str)
    categoryDelete = pyqtSignal(str)
    categoryEdit = pyqtSignal(str, str)

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
                "label": QLabel("Name"),
                "input": QLineEdit(),
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

        _, name, description, _ = row_data

        category_id = db.add_category(name, description)

        if category_id == -1:
            return False

        self.categoryAdd.emit(f"{name} {category_id}")

        self.insert_item_in_table([category_id, name, description, 0])

        return super().add_item()

    def delete_item(self):
        tm = self.get_table_model()

        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
            row = row - deleted_count
            category_id = tm.data(tm.index(row, 0))
            category_name = tm.data(tm.index(row, 1))
            deleted = db.delete_category(int(category_id))

            if not deleted:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Cannot delete category. It is being used by a book.",
                )
                continue

            self.categoryDelete.emit(f"{category_name} {category_id}")
            self.get_table_model().removeRow(row)
            deleted_count += 1

    def edit_item(self):
        row_data = self.extract_form_data()

        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        category_id, name, description, _ = row_data

        old_category = db.get_category(int(category_id))

        if not old_category:
            QMessageBox.critical(
                self, "Error", "An error occurred while getting old category."
            )
            return False

        category = db.edit_category(int(category_id), name, description)

        if not category:
            QMessageBox.critical(
                self, "Error", "An error occurred while editing the category."
            )
            return False

        self.categoryEdit.emit(
            f"{old_category.name} {old_category.id}", f"{name} {category_id}"
        )

        self.edit_item_in_table(row_data)

        return super().edit_item()

    def load_data(self) -> list[list[Any]]:
        categories = db.get_categories()
        data = []

        for category in categories:
            data.append(
                [category.id, category.name, category.description, len(category.books)]
            )

        return data

    def increment_category(self, category_id: str) -> None:
        tm = self.get_table_model()

        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, 0)) == category_id:
                count = int(tm.data(tm.index(row, 3)))
                tm.setData(tm.index(row, 3), count + 1)
                break

    def decrement_category(self, category_id: str) -> None:
        tm = self.get_table_model()

        for row in range(tm.rowCount()):
            if tm.data(tm.index(row, 0)) == category_id:
                count = int(tm.data(tm.index(row, 3)))
                tm.setData(tm.index(row, 3), count - 1)
                break
