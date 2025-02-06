from typing import Any, cast, Tuple, TypedDict
import uuid

from PyQt6.QtWidgets import (
    QWidget,
    QTableView,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QTextEdit,
    QLabel,
    QStackedLayout,
    QComboBox,
)

from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QDate,
    QItemSelectionModel,
)


class FormField(TypedDict):
    label: QLabel
    input: QWidget
    required: bool
    hidden_col: bool
    hidden_field: bool


class BaseModel(QAbstractTableModel):
    def __init__(self, data: list[list[Any]], form_fields: list[FormField]) -> None:
        super().__init__()
        self._data = data or []
        self.headerColumns = [
            (
                field["label"].text()[:-2]
                if field["required"]
                else field["label"].text()[:-1]
            )
            for field in form_fields
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
    def __init__(
        self,
        data: list[list[Any]],
        form_fields: list[FormField],
        hidden_cols: list[int],
    ) -> None:
        super().__init__()
        self.table_view = QTableView()
        self.table_view_model = BaseModel(data, form_fields)
        self.table_view.setModel(self.table_view_model)

        self.selection_model = cast(
            QItemSelectionModel, self.table_view.selectionModel()
        )
        self.selection_model.selectionChanged.connect(self.manage_button_states)
        self.table_view.horizontalHeader().setStretchLastSection(True)  # type: ignore

        for col in hidden_cols:
            self.table_view.setColumnHidden(col, True)

        self.add_button = QPushButton("➕ Add")
        self.edit_button = QPushButton("📝 Edit")
        self.edit_button.setDisabled(True)
        self.delete_button = QPushButton("➖ Delete")
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
    def __init__(
        self,
        form_fields: list[FormField],
        submit_button_name: str,
        hidden_fields: list[int],
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.hidden_fields = hidden_fields

        self.form_fields = form_fields

        button_layout = QHBoxLayout()

        self.submit_button = QPushButton(submit_button_name)
        self.cancel_button = QPushButton("✖️ Cancel")

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(self.form_layout)
        layout.addLayout(button_layout)

    def display_form(self) -> None:
        # Displays form fields to user except id field
        for i, field in enumerate(self.form_fields):
            if i in self.hidden_fields:
                continue

            label = field["label"]
            input = field["input"]

            self.form_layout.addRow(label, input)


class BaseManager(QWidget):
    def __init__(self, form_fields: list[FormField]):
        super().__init__()

        hidden_cols = []
        hidden_fields = []

        for i, field in enumerate(form_fields):
            label = field["label"]
            required = field["required"]
            hidden_col = field["hidden_col"]
            hidden_field = field["hidden_field"]

            label.setText(f"{label.text()}{"*" if required else ""}:")

            if hidden_col:
                hidden_cols.append(i)

            if hidden_field:
                hidden_fields.append(i)

        self.stacked_layout = QStackedLayout(self)
        self.table_view = BaseTableView(self.load_data(), form_fields, hidden_cols)
        self.add_form_view = BaseFormView(form_fields, "➕ Add", hidden_fields)
        self.edit_form_view = BaseFormView(form_fields, "📝 Edit", hidden_fields)

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

        for field, data in zip(self.edit_form_view.form_fields, row_data):
            input = field["input"]

            if isinstance(input, QLineEdit):
                input.setText(data)
            elif isinstance(input, QDateEdit):
                input.setDate(QDate.fromString(data, "dd.MM.yyyy"))
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
        for field in self.add_form_view.form_fields:
            label = field["label"]
            input = field["input"]

            if isinstance(input, QLineEdit) or isinstance(input, QTextEdit):
                input.clear()
            elif isinstance(input, QDateEdit):
                input.setDate(QDate.currentDate())
            elif isinstance(input, QComboBox):
                input.setCurrentIndex(0)

            if label.text() == "ISBN*:":
                cast(QLineEdit, input).setText(uuid.uuid4().hex[:13].upper())

    def extract_form_data(self) -> list[str]:
        row_data: list[str] = []

        for field in self.add_form_view.form_fields:
            input = field["input"]
            required = field["required"]

            text = ""
            if isinstance(input, QLineEdit):
                text = input.text()
            elif isinstance(input, QDateEdit):
                text = input.text()
            elif isinstance(input, QComboBox):
                text = input.currentText()
            elif isinstance(input, QTextEdit):
                text = input.toPlainText()

            text = text.strip()

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
