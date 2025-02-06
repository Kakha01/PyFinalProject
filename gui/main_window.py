from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import QSize
from gui import BookManager, CategoryManager, AuthorManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Library Management System")
        self.setMinimumSize(QSize(500, 500))
        self.setMaximumSize(QSize(800, 600))
        self.tab_widget = QTabWidget(self)

        self.book_manager = BookManager()
        self.category_manager = CategoryManager()
        self.author_manager = AuthorManager()

        self.book_manager.incrementCategoryBooks.connect(
            self.category_manager.increment_category_books
        )
        self.book_manager.incrementAuthorBooks.connect(
            self.author_manager.increment_author_books
        )
        self.book_manager.decrementCategoryBooks.connect(
            self.category_manager.decrement_category_books
        )
        self.book_manager.decrementAuthorBooks.connect(
            self.author_manager.decrement_author_books
        )
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
