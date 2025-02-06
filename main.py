import sys
from PyQt6.QtWidgets import (
    QApplication,
    QPushButton,
    QMainWindow,
    QTabWidget,
    QWidget,
    QTableView,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDateEdit,
    QTextEdit,
    QLabel,
    QStackedLayout,
    QHeaderView,
    QMessageBox,
)
from PyQt6.QtCore import (
    QSize,
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QDate,
    pyqtSignal,
    QItemSelection,
    QItemSelectionModel,
)
from PyQt6.QtGui import QBrush, QColor
from typing import Any, cast
import db
import uuid

FormField = tuple[QLabel, QWidget, bool]


class BaseModel(QAbstractTableModel):
    def __init__(self, data: list[list[Any]], form_fields: list[FormField]) -> None:
        super().__init__()
        self._data = data or []
        self.headerColumns = [
            field.text()[:-2] if required else field.text()[:-1]
            for field, _, required in form_fields
        ]
        self._column_count = len(self.headerColumns)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self._column_count

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            return str(self._data[row][col])

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.headerColumns[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)

        return None

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        self.beginInsertRows(parent, row, row + count - 1)

        for _ in range(count):
            self._data.insert(row, [""] * self.columnCount())

        self.endInsertRows()

        return True

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        self.beginRemoveRows(parent, row, row + count - 1)

        for _ in range(count):
            try:
                del self._data[row]
            except Exception:
                return False

        self.endRemoveRows()

        return True

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()

            if col == -1:
                self._data[row].append(value)
            else:
                self._data[row][col] = value

            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            self.headerDataChanged.emit(
                Qt.Orientation.Horizontal, 0, self.columnCount() - 1
            )

            return True

        return False


class BaseTableView(QWidget):
    def __init__(self, data: list[list[Any]], form_fields: list[FormField]) -> None:
        super().__init__()
        self.table_view = QTableView()
        self.table_view_model = BaseModel(data, form_fields)
        self.table_view.setModel(self.table_view_model)

        self.selection_model = cast(
            QItemSelectionModel, self.table_view.selectionModel()
        )
        self.selection_model.selectionChanged.connect(self.manage_button_states)
        self.table_view.horizontalHeader().setStretchLastSection(True)  # type: ignore
        self.table_view.setColumnHidden(0, True)

        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.edit_button.setDisabled(True)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setDisabled(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(button_layout)

    def manage_button_states(self):
        disable_buttons = True
        selected_rows = self.selection_model.selectedRows()

        if selected_rows:
            disable_buttons = False

        self.edit_button.setDisabled(disable_buttons)
        self.delete_button.setDisabled(disable_buttons)


class BaseFormView(QWidget):
    def __init__(self, form_fields: list[FormField], submit_button_name: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.form_fields = form_fields

        button_layout = QHBoxLayout()

        self.submit_button = QPushButton(submit_button_name)
        self.cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(self.form_layout)
        layout.addLayout(button_layout)

    def display_form(self) -> None:
        # Displays form fields to user except id field
        for label, input, required in self.form_fields[1:]:
            self.form_layout.addRow(label, input)


class BaseManager(QWidget):
    def __init__(self, form_fields: list[FormField]):
        super().__init__()

        for label, input, required in form_fields:
            label.setText(f"{label.text()}{"*" if required else ""}:")

            if isinstance(input, QDateEdit):
                input.setDisplayFormat("dd.MM.yyyy")

        form_fields.insert(0, (QLabel("Id"), QLineEdit(), False))

        self.stacked_layout = QStackedLayout(self)
        self.table_view = BaseTableView(self.load_data(), form_fields)
        self.add_form_view = BaseFormView(form_fields, "Add")
        self.edit_form_view = BaseFormView(form_fields, "Edit")

        self.table_view.add_button.clicked.connect(self.display_add_book_view)
        self.table_view.edit_button.clicked.connect(self.display_edit_book_view)
        self.table_view.delete_button.clicked.connect(self.delete_item)
        self.add_form_view.cancel_button.clicked.connect(self.reset_form)
        self.add_form_view.submit_button.clicked.connect(self.add_item)
        self.edit_form_view.cancel_button.clicked.connect(self.reset_form)
        self.edit_form_view.submit_button.clicked.connect(self.edit_item)

        self.stacked_layout.addWidget(self.table_view)
        self.stacked_layout.addWidget(self.add_form_view)
        self.stacked_layout.addWidget(self.edit_form_view)

    def display_table_view(self) -> None:
        self.stacked_layout.setCurrentIndex(0)

    def display_add_book_view(self) -> None:
        self.add_form_view.display_form()
        self.stacked_layout.setCurrentIndex(1)

    def display_edit_book_view(self) -> None:
        self.edit_form_view.display_form()

        selected_rows = self.get_selection_model().selectedRows()

        row = selected_rows[0].row()

        row_data: list[str] = []

        for col in range(self.get_table_model().columnCount()):
            index = self.get_table_model().index(row, col)
            data = self.get_table_model().data(index, Qt.ItemDataRole.DisplayRole)
            row_data.append(data)

        for (_, input, required), data in zip(
            self.edit_form_view.form_fields, row_data
        ):
            if isinstance(input, QLineEdit):
                input.setText(data)
            elif isinstance(input, QDateEdit):
                input.setDate(QDate.fromString(data, "dd.MM.yyyy"))
            elif isinstance(input, QSpinBox):
                input.setValue(int(data))
            elif isinstance(input, QComboBox):
                input.setCurrentText(data)
            elif isinstance(input, QTextEdit):
                input.setPlainText(data)

        self.stacked_layout.setCurrentIndex(2)

    def delete_item(self) -> None:
        # To be implemented by parent class

        return

    def add_item(self) -> bool:
        # To be implemented by parent class

        self.reset_form()
        return True

    def edit_item(self) -> bool:
        # To be implemented by parent class

        self.reset_form()

        return True

    def reset_form(self) -> None:
        self.display_table_view()
        self.reset_form_fields()

    def reset_form_fields(self) -> None:
        for label, input, _ in self.add_form_view.form_fields:
            if isinstance(input, QLineEdit) or isinstance(input, QTextEdit):
                input.clear()
            elif isinstance(input, QDateEdit):
                input.setDate(QDate.currentDate())
            elif isinstance(input, QSpinBox):
                input.setValue(0)
            elif isinstance(input, QComboBox):
                input.setCurrentIndex(0)

            if label.text() == "ISBN Number*:":
                cast(QLineEdit, input).setText(uuid.uuid4().hex[:13].upper())

    def extract_form_data(self) -> list[str]:
        row_data: list[str] = []

        for _, input, required in self.add_form_view.form_fields:
            text = ""
            if isinstance(input, QLineEdit):
                text = input.text()
            elif isinstance(input, QDateEdit):
                text = input.text()
            elif isinstance(input, QSpinBox):
                text = input.text()
            elif isinstance(input, QComboBox):
                text = input.currentText()
            elif isinstance(input, QTextEdit):
                text = input.toPlainText()

            if required and text == "":
                return []

            row_data.append(text)

        return row_data

    def insert_item_in_table(self, row_data: list[Any]) -> bool:
        row = self.get_table_model().rowCount()

        self.get_table_model().insertRow(row)

        for col, data in enumerate(row_data):
            index = self.get_table_model().index(row, col)
            self.get_table_model().setData(index, data)

        return True

    def edit_item_in_table(self, row_data: list[Any]) -> bool:
        row = self.get_selection_model().selectedRows()[0].row()

        for col, data in enumerate(row_data):
            index = self.get_table_model().index(row, col)
            self.get_table_model().setData(index, data)

        return True

    def get_table_model(self):
        return self.table_view.table_view_model

    def get_table(self):
        return self.table_view.table_view

    def get_selection_model(self):
        return self.table_view.selection_model

    def load_data(self) -> list[list[Any]]:
        return []


class BookManager(BaseManager):
    def __init__(self):
        self.AUTHOR_COL = 2
        self.CATEGORY_COL = 3
        self.form_fields: list[FormField] = [
            (QLabel("Title"), QLineEdit(), True),
            (QLabel("Author"), QComboBox(), True),
            (QLabel("Category"), QComboBox(), True),
            (QLabel("ISBN Number"), QLineEdit(), True),
            (QLabel("Release Date"), QDateEdit(QDate.currentDate()), True),
            (QLabel("Description"), QTextEdit(), False),
        ]

        super().__init__(self.form_fields)
        self.get_author().addItems(self.load_authors())
        self.get_category().addItems(self.load_categories())
        self.get_isbn().setText(uuid.uuid4().hex[:13].upper())
        self.get_isbn().setReadOnly(True)

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

    def load_data(self) -> list[list[Any]]:
        books = db.get_books()
        data = []

        for book in books:
            print(book.release_date)
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

    def load_authors(self):
        authors = db.get_authors()
        return [
            f"{author.first_name} {author.last_name} {author.id}" for author in authors
        ]

    def load_categories(self):
        categories = db.get_categories()
        return [f"{category.name} {category.id}" for category in categories]

    def get_isbn(self):
        return cast(QLineEdit, self.form_fields[4][1])


class CategoryManager(BaseManager):
    categoryAdd = pyqtSignal(str)
    categoryDelete = pyqtSignal(str)
    categoryEdit = pyqtSignal(str, str)

    def __init__(self):
        self.form_fields: list[FormField] = [
            (QLabel("Name"), QLineEdit(), True),
            (QLabel("Description"), QTextEdit(), False),
        ]
        super().__init__(self.form_fields)

    def add_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            return False

        _, name, description = row_data

        category_id = db.add_category(name, description)

        if category_id == -1:
            return False

        self.categoryAdd.emit(f"{name} {category_id}")

        self.insert_item_in_table([category_id, name, description])

        return super().add_item()

    def delete_item(self):
        tm = self.get_table_model()

        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
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
            self.get_table_model().removeRow(row - deleted_count)
            deleted_count += 1

    def edit_item(self):
        row_data = self.extract_form_data()

        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        category_id, name, description = row_data

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

        print(f"{old_category.name} {old_category.id}", f"{name} {category_id}")

        self.edit_item_in_table(row_data)

        return super().edit_item()

    def load_data(self) -> list[list[Any]]:
        categories = db.get_categories()
        data = []

        for category in categories:
            data.append([category.id, category.name, category.description])

        return data


class AuthorManager(BaseManager):
    authorAdd = pyqtSignal(str)
    authorDelete = pyqtSignal(str)
    authorEdit = pyqtSignal(str, str)

    def __init__(self):
        self.form_fields: list[FormField] = [
            (QLabel("First Name"), QLineEdit(), True),
            (QLabel("Last Name"), QLineEdit(), True),
            (QLabel("Biography"), QTextEdit(), False),
        ]
        super().__init__(self.form_fields)

    def add_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            return False

        _, first_name, last_name, bio = row_data

        author_id = db.add_author(first_name, last_name, bio)

        if author_id == -1:
            return False

        self.authorAdd.emit(f"{first_name} {last_name} {author_id}")

        self.insert_item_in_table([author_id, first_name, last_name, bio])

        return super().add_item()

    def delete_item(self):
        tm = self.get_table_model()
        selected_rows = self.get_selection_model().selectedRows()
        rows = [row.row() for row in selected_rows]
        rows.sort()
        deleted_count = 0

        for row in rows:
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
            self.get_table_model().removeRow(row - deleted_count)

            deleted_count += 1

    def edit_item(self) -> bool:
        row_data = self.extract_form_data()

        if not row_data:
            QMessageBox.critical(
                self, "Error", "Please fill in all the required fields."
            )
            return False

        author_id, first_name, last_name, bio = row_data

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

        return super().edit_item()

    def load_data(self) -> list[list[Any]]:
        authors = db.get_authors()
        data = []

        for author in authors:
            data.append([author.id, author.first_name, author.last_name, author.bio])

        return data


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Library Management System")
        self.setFixedSize(QSize(500, 500))
        self.tab_widget = QTabWidget(self)

        self.book_manager = BookManager()
        self.category_manager = CategoryManager()
        self.author_manager = AuthorManager()

        self.category_manager.categoryAdd.connect(self.book_manager.add_category)
        self.category_manager.categoryDelete.connect(self.book_manager.delete_category)
        self.category_manager.categoryEdit.connect(self.book_manager.edit_category)
        self.author_manager.authorAdd.connect(self.book_manager.add_author)
        self.author_manager.authorDelete.connect(self.book_manager.delete_author)
        self.author_manager.authorEdit.connect(self.book_manager.edit_author)

        self.tab_widget.addTab(self.book_manager, "Book Manager")
        self.tab_widget.addTab(self.category_manager, "Category Manager")
        self.tab_widget.addTab(self.author_manager, "Author Manager")

        self.setCentralWidget(self.tab_widget)


if __name__ == "__main__":
    db.create_all()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
