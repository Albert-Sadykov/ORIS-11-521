"""Task Manager 2.0: сигналы, слоты, диалоги и сохранение задач."""

import json
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Task Manager 2.0\nУчебное приложение на PyQt6."))
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class TaskManagerWindow(QMainWindow):
    task_created = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.tasks: list[dict[str, str]] = []
        self.storage_path = Path(__file__).with_name("tasks.json")

        self.setWindowTitle("Task Manager 2.0")
        self.resize(620, 680)
        self._build_ui()
        self._connect_signals()
        self.setStyleSheet(self._stylesheet())
        self.load_tasks()
        self.refresh_task_list()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        main_layout.addWidget(QLabel("Название задачи"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: подготовить презентацию")
        main_layout.addWidget(self.title_input)

        self.title_count_label = QLabel("Название: 0 символов")
        main_layout.addWidget(self.title_count_label)

        main_layout.addWidget(QLabel("Описание"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Необязательное описание задачи")
        self.description_input.setFixedHeight(100)
        main_layout.addWidget(self.description_input)

        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Приоритет:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Низкий", "Средний", "Высокий"])
        self.priority_combo.setCurrentText("Средний")
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        main_layout.addLayout(priority_layout)

        form_buttons = QHBoxLayout()
        self.add_button = QPushButton("Добавить задачу")
        self.edit_button = QPushButton("Изменить выбранную")
        self.edit_button.setEnabled(False)
        form_buttons.addWidget(self.add_button)
        form_buttons.addWidget(self.edit_button)
        main_layout.addLayout(form_buttons)

        main_layout.addWidget(QLabel("Список задач"))
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.task_list)

        list_buttons = QHBoxLayout()
        self.delete_button = QPushButton("Удалить выбранную")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.setEnabled(False)
        self.clear_button = QPushButton("Очистить список")
        self.clear_button.setEnabled(False)
        self.about_button = QPushButton("О программе")
        list_buttons.addWidget(self.delete_button)
        list_buttons.addWidget(self.clear_button)
        list_buttons.addStretch()
        list_buttons.addWidget(self.about_button)
        main_layout.addLayout(list_buttons)

        self.status_label = QLabel("Задач: 0")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)

    def _connect_signals(self) -> None:
        self.add_button.clicked.connect(self.add_task)
        self.edit_button.clicked.connect(self.edit_selected_task)
        self.delete_button.clicked.connect(self.delete_selected_task)
        self.clear_button.clicked.connect(self.clear_task_list)
        self.about_button.clicked.connect(self.show_about_dialog)
        self.title_input.textChanged.connect(self.update_title_count)
        self.task_list.itemSelectionChanged.connect(self.update_action_buttons)
        self.task_list.itemDoubleClicked.connect(self.load_selected_task_into_form)
        self.task_created.connect(self.update_status)

    def add_task(self) -> None:
        task = self.task_from_form()
        if task is None:
            return

        self.tasks.append(task)
        self.save_tasks()
        self.refresh_task_list()
        self.clear_form()
        self.task_created.emit()

    def edit_selected_task(self) -> None:
        row = self.task_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Изменение задачи", "Сначала выберите задачу.")
            return

        task = self.task_from_form()
        if task is None:
            return

        self.tasks[row] = task
        self.save_tasks()
        self.refresh_task_list()
        self.task_list.setCurrentRow(row)
        self.status_label.setText(f"Задача изменена. Задач: {len(self.tasks)}")

    def delete_selected_task(self) -> None:
        row = self.task_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Удаление задачи", "Сначала выберите задачу.")
            return

        answer = QMessageBox.question(
            self,
            "Удаление задачи",
            "Удалить выбранную задачу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        del self.tasks[row]
        self.save_tasks()
        self.refresh_task_list()
        self.status_label.setText(f"Задача удалена. Задач: {len(self.tasks)}")

    def clear_task_list(self) -> None:
        if not self.tasks:
            return

        answer = QMessageBox.question(
            self,
            "Очистка списка",
            "Удалить все задачи? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.tasks.clear()
        self.save_tasks()
        self.refresh_task_list()
        self.status_label.setText("Список очищен. Задач: 0")

    def task_from_form(self) -> dict[str, str] | None:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Новая задача", "Введите название задачи.")
            return None
        return {
            "title": title,
            "description": self.description_input.toPlainText().strip(),
            "priority": self.priority_combo.currentText(),
        }

    def refresh_task_list(self) -> None:
        self.task_list.clear()
        for task in self.tasks:
            item = QListWidgetItem(f"[{task['priority']}] {task['title']}")
            item.setData(Qt.ItemDataRole.UserRole, task)
            self.task_list.addItem(item)
        self.update_action_buttons()

    def load_selected_task_into_form(self, item: QListWidgetItem) -> None:
        task = item.data(Qt.ItemDataRole.UserRole)
        self.title_input.setText(task["title"])
        self.description_input.setPlainText(task["description"])
        self.priority_combo.setCurrentText(task["priority"])

    def clear_form(self) -> None:
        self.title_input.clear()
        self.description_input.clear()
        self.priority_combo.setCurrentText("Средний")

    def update_title_count(self, text: str) -> None:
        self.title_count_label.setText(f"Название: {len(text)} символов")

    def update_status(self) -> None:
        self.status_label.setText(f"Задач: {len(self.tasks)}")

    def update_action_buttons(self) -> None:
        has_selection = self.task_list.currentRow() >= 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.clear_button.setEnabled(bool(self.tasks))

    def show_about_dialog(self) -> None:
        AboutDialog(self).exec()

    def load_tasks(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self, "Загрузка задач", f"Не удалось прочитать tasks.json:\n{error}")
            return
        if not isinstance(data, list):
            QMessageBox.warning(self, "Загрузка задач", "tasks.json должен содержать список задач.")
            return

        self.tasks = [
            {
                "title": str(task.get("title", "")),
                "description": str(task.get("description", "")),
                "priority": str(task.get("priority", "Средний")),
            }
            for task in data
            if isinstance(task, dict) and str(task.get("title", "")).strip()
        ]

    def save_tasks(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps(self.tasks, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            QMessageBox.warning(self, "Сохранение задач", f"Не удалось сохранить tasks.json:\n{error}")

    @staticmethod
    def _stylesheet() -> str:
        return """
            QMainWindow { background: #f4f7fb; }
            QLabel { color: #25324a; font-size: 14px; }
            QLineEdit, QTextEdit, QComboBox, QListWidget {
                background: white;
                border: 1px solid #b8c4d8;
                border-radius: 6px;
                padding: 7px;
                selection-background-color: #b9dcff;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QListWidget:focus {
                border: 2px solid #3578c9;
            }
            QPushButton {
                background: #3578c9;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover { background: #245d9e; }
            QPushButton:disabled { background: #aeb9c8; color: #e9edf3; }
            QPushButton#deleteButton { background: #c74d55; }
            QPushButton#deleteButton:hover { background: #a53b43; }
            QLabel#statusLabel { font-weight: bold; font-size: 15px; padding: 5px; }
        """


def main() -> None:
    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
