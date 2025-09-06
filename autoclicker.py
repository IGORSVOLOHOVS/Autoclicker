import sys
import threading
import time
import pyautogui
import random
import json
import pathlib
import keyboard
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QKeySequence
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QMessageBox, QCheckBox, QStatusBar, QGroupBox,
                             QHBoxLayout, QFileDialog)

class HotkeyThread(QThread):
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    get_pos_signal = pyqtSignal()
    
    def __init__(self, hotkeys):
        super().__init__()
        self.hotkeys = hotkeys

    def run(self):
        keyboard.add_hotkey(self.hotkeys['start'], self.start_signal.emit)
        keyboard.add_hotkey(self.hotkeys['stop'], self.stop_signal.emit)
        keyboard.add_hotkey(self.hotkeys['get_pos'], self.get_pos_signal.emit)
        keyboard.wait()

class ClickerThread(QThread):
    update_counter = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self._is_running = True
        self.clicks_done = 0

    def run(self):
        while self._is_running:
            x, y = self.settings['click_x'], self.settings['click_y']
            
            if self.settings['random_offset_enabled']:
                offset_x = random.randint(-self.settings['random_offset_range'], self.settings['random_offset_range'])
                offset_y = random.randint(-self.settings['random_offset_range'], self.settings['random_offset_range'])
                x += offset_x
                y += offset_y
            
            if self.settings['fixed_pos_enabled']:
                pyautogui.moveTo(x, y)
            
            try:
                if self.settings['click_type'] == "Один клик":
                    pyautogui.click(button=self.settings['click_button'])
                elif self.settings['click_type'] == "Двойной клик":
                    pyautogui.doubleClick(button=self.settings['click_button'])
                elif self.settings['click_type'] == "Перетаскивание":
                    pyautogui.mouseDown(button=self.settings['click_button'])
                    time.sleep(self.settings['drag_duration_sec'])
                    pyautogui.mouseUp(button=self.settings['click_button'])
            except Exception as e:
                print(f"Ошибка pyautogui: {e}")

            self.clicks_done += 1
            self.update_counter.emit(self.clicks_done)
            
            if self.settings['click_count'] != 0 and self.clicks_done >= self.settings['click_count']:
                self.stop()
                break
            
            sleep_time = self.settings['interval_sec']
            if self.settings['random_interval_enabled']:
                sleep_time += random.uniform(-self.settings['random_interval_range'], self.settings['random_interval_range']) / 1000.0
                if sleep_time < 0: sleep_time = 0.001
            
            time.sleep(sleep_time)
            
        self.finished.emit()

    def stop(self):
        self._is_running = False

class AutoClicker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Clicker Pro")
        self.resize(500, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: Arial;
                font-size: 12pt;
            }
            QGroupBox {
                border: 2px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                background-color: #34495e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #ecf0f1;
            }
            QLineEdit, QComboBox {
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 5px;
                background-color: #3b506b;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #20639b;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QStatusBar {
                border-top: 1px solid #34495e;
                background-color: #2c3e50;
                color: #bdc3c7;
            }
        """)
        self.clicking = False
        self.click_thread = None
        self.is_getting_position = False
        self.config_dir = pathlib.Path("configs")
        self.last_config_file = pathlib.Path("last_config.json")
        self.init_hotkeys()
        self.init_ui()
        self.register_global_hotkeys()
        self.load_last_used_settings()
        self.populate_config_list()
        
    def closeEvent(self, event):
        keyboard.unhook_all()
        event.accept()

    def init_hotkeys(self):
        self.hotkeys = {
            'start': 'F6',
            'stop': 'F7',
            'get_pos': 'F8'
        }
        self.key_inputs = {}
        
    def register_global_hotkeys(self):
        self.hotkey_thread = HotkeyThread(self.hotkeys)
        self.hotkey_thread.start_signal.connect(self.start_clicking)
        self.hotkey_thread.stop_signal.connect(self.stop_clicking)
        self.hotkey_thread.get_pos_signal.connect(self.get_position)
        self.hotkey_thread.start()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        click_group = QGroupBox("Настройки клика")
        click_group_layout = QGridLayout()
        click_group.setLayout(click_group_layout)

        click_group_layout.addWidget(QLabel("Интервал:"), 0, 0)
        interval_layout = QHBoxLayout()
        self.interval_input = QLineEdit("100")
        self.interval_unit_combo = QComboBox()
        self.interval_unit_combo.addItems(["ms", "s"])
        interval_layout.addWidget(self.interval_input)
        interval_layout.addWidget(self.interval_unit_combo)
        click_group_layout.addLayout(interval_layout, 0, 1, 1, 2)

        click_group_layout.addWidget(QLabel("Количество кликов:"), 1, 0)
        self.click_count_input = QLineEdit("0")
        self.click_count_input.setToolTip("0 для бесконечных кликов")
        click_group_layout.addWidget(self.click_count_input, 1, 1, 1, 2)
        
        click_group_layout.addWidget(QLabel("Тип мыши:"), 2, 0)
        self.mouse_button_combo = QComboBox()
        self.mouse_button_combo.addItems(["Левая", "Правая", "Средняя"])
        click_group_layout.addWidget(self.mouse_button_combo, 2, 1, 1, 2)

        click_group_layout.addWidget(QLabel("Тип клика:"), 3, 0)
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems(["Один клик", "Двойной клик", "Перетаскивание"])
        self.click_type_combo.currentIndexChanged.connect(self.toggle_drag_duration)
        click_group_layout.addWidget(self.click_type_combo, 3, 1, 1, 2)

        self.drag_duration_label = QLabel("Длит. перетаскивания (ms):")
        click_group_layout.addWidget(self.drag_duration_label, 4, 0)
        self.drag_duration_input = QLineEdit("500")
        self.drag_duration_input.setEnabled(False)
        click_group_layout.addWidget(self.drag_duration_input, 4, 1, 1, 2)
        
        main_layout.addWidget(click_group)

        random_group = QGroupBox("Случайные настройки")
        random_group_layout = QGridLayout()
        random_group.setLayout(random_group_layout)
        
        self.fixed_pos_checkbox = QCheckBox("Фиксированное положение")
        self.fixed_pos_checkbox.stateChanged.connect(self.toggle_fixed_pos_fields)
        random_group_layout.addWidget(self.fixed_pos_checkbox, 0, 0)
        self.coord_x_input = QLineEdit()
        self.coord_x_input.setPlaceholderText("X")
        self.coord_y_input = QLineEdit()
        self.coord_y_input.setPlaceholderText("Y")
        random_group_layout.addWidget(self.coord_x_input, 0, 1)
        random_group_layout.addWidget(self.coord_y_input, 0, 2)
        
        self.random_offset_checkbox = QCheckBox("Случайное смещение (± px)")
        self.random_offset_checkbox.stateChanged.connect(self.toggle_random_offset)
        self.random_offset_input = QLineEdit("5")
        random_group_layout.addWidget(self.random_offset_checkbox, 1, 0)
        random_group_layout.addWidget(self.random_offset_input, 1, 1, 1, 2)
        
        self.random_interval_checkbox = QCheckBox("Случайный интервал (± ms)")
        self.random_interval_checkbox.stateChanged.connect(self.toggle_random_interval)
        self.random_interval_input = QLineEdit("10")
        random_group_layout.addWidget(self.random_interval_checkbox, 2, 0)
        random_group_layout.addWidget(self.random_interval_input, 2, 1, 1, 2)
        
        self.toggle_fixed_pos_fields(self.fixed_pos_checkbox.checkState())
        self.toggle_random_offset(self.random_offset_checkbox.checkState())
        self.toggle_random_interval(self.random_interval_checkbox.checkState())

        main_layout.addWidget(random_group)
        
        hotkey_group = QGroupBox("Горячие клавиши")
        hotkey_group_layout = QGridLayout()
        hotkey_group.setLayout(hotkey_group_layout)
        
        hotkey_group_layout.addWidget(QLabel("Старт:"), 0, 0)
        self.start_key_input = QLineEdit(self.hotkeys['start'])
        self.start_key_input.setReadOnly(True)
        hotkey_group_layout.addWidget(self.start_key_input, 0, 1)

        hotkey_group_layout.addWidget(QLabel("Стоп:"), 1, 0)
        self.stop_key_input = QLineEdit(self.hotkeys['stop'])
        self.stop_key_input.setReadOnly(True)
        hotkey_group_layout.addWidget(self.stop_key_input, 1, 1)

        hotkey_group_layout.addWidget(QLabel("Получить позицию:"), 2, 0)
        self.get_pos_key_input = QLineEdit(self.hotkeys['get_pos'])
        self.get_pos_key_input.setReadOnly(True)
        hotkey_group_layout.addWidget(self.get_pos_key_input, 2, 1)

        main_layout.addWidget(hotkey_group)

        # Группа управления конфигурациями
        config_group = QGroupBox("Управление конфигурациями")
        config_group_layout = QGridLayout()
        config_group.setLayout(config_group_layout)
        
        config_group_layout.addWidget(QLabel("Доступные конфигурации:"), 0, 0)
        self.config_combo = QComboBox()
        config_group_layout.addWidget(self.config_combo, 0, 1)
        
        load_selected_button = QPushButton("Загрузить")
        load_selected_button.clicked.connect(self.load_selected_config)
        config_group_layout.addWidget(load_selected_button, 0, 2)
        
        main_layout.addWidget(config_group)

        settings_buttons_layout = QGridLayout()
        save_button = QPushButton("Сохранить настройки")
        save_button.clicked.connect(self.save_settings)
        settings_buttons_layout.addWidget(save_button, 0, 0)
        load_button = QPushButton("Загрузить файл")
        load_button.clicked.connect(self.load_settings)
        settings_buttons_layout.addWidget(load_button, 0, 1)
        main_layout.addLayout(settings_buttons_layout)

        status_layout = QGridLayout()
        
        self.start_button = QPushButton("Старт")
        self.start_button.clicked.connect(self.start_clicking)
        self.stop_button = QPushButton("Стоп")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_clicking)
        
        self.clicks_done_label = QLabel("Сделано кликов: 0")
        
        status_layout.addWidget(self.start_button, 0, 0)
        status_layout.addWidget(self.stop_button, 0, 1)
        status_layout.addWidget(self.clicks_done_label, 1, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addLayout(status_layout)

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)

    def hotkeys_to_string(self, key_code):
        return QKeySequence(key_code).toString() if key_code else ""

    def toggle_drag_duration(self, index):
        self.drag_duration_input.setEnabled(self.click_type_combo.currentText() == "Перетаскивание")
        self.drag_duration_label.setEnabled(self.click_type_combo.currentText() == "Перетаскивание")

    def toggle_fixed_pos_fields(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.coord_x_input.setEnabled(enabled)
        self.coord_y_input.setEnabled(enabled)
        self.random_offset_checkbox.setEnabled(enabled)
        self.random_offset_input.setEnabled(enabled and self.random_offset_checkbox.isChecked())

    def toggle_random_offset(self, state):
        self.random_offset_input.setEnabled(state == Qt.CheckState.Checked.value)

    def toggle_random_interval(self, state):
        self.random_interval_input.setEnabled(state == Qt.CheckState.Checked.value)

    def get_position(self):
        self._capture_position()
        
    def _capture_position(self):
        x, y = pyautogui.position()
        self.coord_x_input.setText(str(x))
        self.coord_y_input.setText(str(y))
        self.status_bar.showMessage(f"Координаты: X={x}, Y={y}", 3000)

    def mousePressEvent(self, event):
        if hasattr(self, 'is_getting_position') and self.is_getting_position and event.button() == Qt.MouseButton.LeftButton:
            x, y = QCursor.pos().x(), QCursor.pos().y()
            self.coord_x_input.setText(str(x))
            self.coord_y_input.setText(str(y))
            self.status_bar.showMessage(f"Координаты: X={x}, Y={y}", 3000)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.is_getting_position = False

    def start_clicking(self):
        if self.clicking:
            return

        settings = self.get_current_settings()
        if not settings:
            return

        self.clicking = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage("Запуск кликов...", 0)

        self.click_thread = ClickerThread(settings)
        self.click_thread.update_counter.connect(self.update_click_counter)
        self.click_thread.finished.connect(self.stop_clicking)
        self.click_thread.start()

    def get_current_settings(self):
        settings = {}
        try:
            interval = int(self.interval_input.text())
            if self.interval_unit_combo.currentText() == "s":
                settings['interval_sec'] = interval
            else:
                settings['interval_sec'] = interval / 1000.0
            
            settings['click_count'] = int(self.click_count_input.text())
            settings['click_type'] = self.click_type_combo.currentText()
            settings['fixed_pos_enabled'] = self.fixed_pos_checkbox.isChecked()
            settings['random_offset_enabled'] = self.random_offset_checkbox.isChecked()
            settings['random_interval_enabled'] = self.random_interval_checkbox.isChecked()

            if settings['fixed_pos_enabled']:
                settings['click_x'] = int(self.coord_x_input.text())
                settings['click_y'] = int(self.coord_y_input.text())
            else:
                settings['click_x'], settings['click_y'] = pyautogui.position()
            
            if settings['random_offset_enabled']:
                settings['random_offset_range'] = int(self.random_offset_input.text())
            
            if settings['random_interval_enabled']:
                settings['random_interval_range'] = int(self.random_interval_input.text())
            
            button_map = {"Левая": "left", "Правая": "right", "Средняя": "middle"}
            settings['click_button'] = button_map[self.mouse_button_combo.currentText()]
            
            if settings['click_type'] == "Перетаскивание":
                settings['drag_duration_sec'] = int(self.drag_duration_input.text()) / 1000
            
            return settings
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Проверьте правильность числовых значений.")
            return None

    def stop_clicking(self):
        if not self.clicking:
            return
        if self.click_thread and self.click_thread.isRunning():
            self.click_thread.stop()
            self.click_thread.wait()
        
        self.clicking = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("Клики остановлены.", 3000)

    def update_click_counter(self, count):
        self.clicks_done_label.setText(f"Сделано кликов: {count}")

    def populate_config_list(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_combo.clear()
        config_files = list(self.config_dir.glob("*.json"))
        if not config_files:
            self.config_combo.addItem("Нет сохраненных файлов")
        else:
            for file in config_files:
                self.config_combo.addItem(file.name)

    def save_last_config_path(self, file_path):
        try:
            with open(self.last_config_file, 'w') as f:
                f.write(file_path)
        except Exception as e:
            print(f"Не удалось сохранить путь к последней конфигурации: {e}")

    def load_last_used_settings(self):
        if self.last_config_file.exists():
            try:
                with open(self.last_config_file, 'r') as f:
                    file_path = f.read().strip()
                    if file_path:
                        self.load_settings(file_path)
                        self.status_bar.showMessage("Загружена последняя конфигурация.", 3000)
            except Exception as e:
                self.status_bar.showMessage(f"Ошибка загрузки последней конфигурации: {e}", 5000)

    def load_selected_config(self):
        file_name = self.config_combo.currentText()
        if file_name and file_name != "Нет сохраненных файлов":
            file_path = self.config_dir / file_name
            self.load_settings(file_path)

    def save_settings(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить настройки", str(self.config_dir), "JSON Files (*.json)")
        if file_path:
            settings = {
                'interval': self.interval_input.text(),
                'interval_unit': self.interval_unit_combo.currentText(),
                'click_count': self.click_count_input.text(),
                'mouse_button': self.mouse_button_combo.currentText(),
                'click_type': self.click_type_combo.currentText(),
                'drag_duration': self.drag_duration_input.text(),
                'fixed_pos_enabled': self.fixed_pos_checkbox.isChecked(),
                'coord_x': self.coord_x_input.text(),
                'coord_y': self.coord_y_input.text(),
                'random_offset_enabled': self.random_offset_checkbox.isChecked(),
                'random_offset_range': self.random_offset_input.text(),
                'random_interval_enabled': self.random_interval_checkbox.isChecked(),
                'random_interval_range': self.random_interval_input.text(),
                'hotkeys': self.hotkeys
            }
            try:
                with open(file_path, 'w') as f:
                    json.dump(settings, f, indent=4)
                self.save_last_config_path(file_path)
                self.populate_config_list()
                self.status_bar.showMessage("Настройки сохранены.", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка сохранения", f"Не удалось сохранить файл: {e}")

    def load_settings(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Загрузить настройки", str(self.config_dir), "JSON Files (*.json)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings = json.load(f)
                
                self.interval_input.setText(settings.get('interval', "100"))
                self.interval_unit_combo.setCurrentText(settings.get('interval_unit', "ms"))
                self.click_count_input.setText(settings.get('click_count', "0"))
                self.mouse_button_combo.setCurrentText(settings.get('mouse_button', "Левая"))
                self.click_type_combo.setCurrentText(settings.get('click_type', "Один клик"))
                self.drag_duration_input.setText(settings.get('drag_duration', "500"))
                self.fixed_pos_checkbox.setChecked(settings.get('fixed_pos_enabled', False))
                self.coord_x_input.setText(settings.get('coord_x', ""))
                self.coord_y_input.setText(settings.get('coord_y', ""))
                self.random_offset_checkbox.setChecked(settings.get('random_offset_enabled', False))
                self.random_offset_input.setText(settings.get('random_offset_range', "5"))
                self.random_interval_checkbox.setChecked(settings.get('random_interval_enabled', False))
                self.random_interval_input.setText(settings.get('random_interval_range', "10"))
                
                if 'hotkeys' in settings:
                    self.hotkeys = settings['hotkeys']
                    self.start_key_input.setText(self.hotkeys['start'])
                    self.stop_key_input.setText(self.hotkeys['stop'])
                    self.get_pos_key_input.setText(self.hotkeys['get_pos'])
                    self.register_global_hotkeys()

                self.save_last_config_path(file_path)
                self.status_bar.showMessage("Настройки загружены.", 3000)
            except FileNotFoundError:
                QMessageBox.warning(self, "Ошибка загрузки", "Файл не найден.")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка загрузки", f"Не удалось загрузить файл: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    autoclicker = AutoClicker()
    autoclicker.show()
    sys.exit(app.exec())
