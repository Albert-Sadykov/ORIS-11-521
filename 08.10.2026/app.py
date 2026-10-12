import sys

from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TaskManagerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.tasks: list[dict[str, object]] = []

        self.setWindowTitle("Менеджер задач")
        self.resize(560, 620)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        form_layout = QGridLayout()
        main_layout.addLayout(form_layout)

        task_label = QLabel("Задача:")
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Введите название задачи")
        form_layout.addWidget(task_label, 0, 0)
        form_layout.addWidget(self.task_input, 0, 1)

        description_label = QLabel("Описание:")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Введите описание задачи")
        form_layout.addWidget(description_label, 1, 0)
        form_layout.addWidget(self.description_input, 1, 1)

        priority_group_box = QGroupBox("Приоритет")
        priority_layout = QHBoxLayout()
        priority_group_box.setLayout(priority_layout)

        self.low_priority = QRadioButton("Низкий")
        self.medium_priority = QRadioButton("Средний")
        self.high_priority = QRadioButton("Высокий")
        self.medium_priority.setChecked(True)

        self.priority_group = QButtonGroup(self)
        for button in (self.low_priority, self.medium_priority, self.high_priority):
            self.priority_group.addButton(button)
            priority_layout.addWidget(button)
        main_layout.addWidget(priority_group_box)

        settings_group_box = QGroupBox("Дополнительные настройки")
        settings_layout = QVBoxLayout()
        settings_group_box.setLayout(settings_layout)

        self.important_checkbox = QCheckBox("Важная задача")
        self.notification_checkbox = QCheckBox("Отправить уведомление")
        settings_layout.addWidget(self.important_checkbox)
        settings_layout.addWidget(self.notification_checkbox)
        main_layout.addWidget(settings_group_box)

        buttons_layout = QHBoxLayout()
        self.create_button = QPushButton("Создать задачу")
        self.clear_button = QPushButton("Очистить")
        self.create_button.clicked.connect(self.create_task)
        self.clear_button.clicked.connect(self.clear_form)
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.clear_button)
        main_layout.addLayout(buttons_layout)

        self.status_label = QLabel("Статус: Готово")
        self.counter_label = QLabel("Создано задач: 0")
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.counter_label)

        result_label = QLabel("Созданная задача:")
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Здесь появится созданная задача.")
        main_layout.addWidget(result_label)
        main_layout.addWidget(self.result_output)

    def create_task(self) -> None:
        task_name = self.task_input.text().strip()
        if not task_name:
            QMessageBox.warning(self, "Менеджер задач", "Введите название задачи.")
            return

        selected_priority = self.priority_group.checkedButton()
        priority = selected_priority.text() if selected_priority else "Не выбран"
        task = {
            "name": task_name,
            "description": self.description_input.toPlainText().strip(),
            "priority": priority,
            "important": self.important_checkbox.isChecked(),
            "notification": self.notification_checkbox.isChecked(),
        }
        self.tasks.append(task)

        result = (
            f"Задача: {task['name']}\n"
            f"Описание: {task['description'] or 'Нет описания'}\n"
            f"Приоритет: {task['priority']}\n"
            f"Важная задача: {'Да' if task['important'] else 'Нет'}\n"
            f"Отправить уведомление: {'Да' if task['notification'] else 'Нет'}"
        )
        self.result_output.setPlainText(result)
        self.status_label.setText("Статус: Задача создана")
        self.counter_label.setText(f"Создано задач: {len(self.tasks)}")

        print(result)

    def clear_form(self) -> None:
        self.task_input.clear()
        self.description_input.clear()
        self.medium_priority.setChecked(True)
        self.important_checkbox.setChecked(False)
        self.notification_checkbox.setChecked(False)
        self.result_output.clear()
        self.status_label.setText("Статус: Готово")


def main() -> None:
    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
