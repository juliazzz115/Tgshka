"""
Система обязательных desktop уведомлений
Окно нельзя закрыть без подтверждения прочтения
"""
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import threading
import queue


class MandatoryNotification:
    def __init__(self):
        """Инициализация системы уведомлений"""
        self.root = None
        self.notification_queue = queue.Queue()
        self.current_message = None
        self.on_confirm_callback = None
        self.is_running = False

    def set_confirm_callback(self, callback):
        """
        Установить callback для подтверждения прочтения

        Args:
            callback: Функция, которая будет вызываться при подтверждении
                     Должна принимать параметр: message_id
        """
        self.on_confirm_callback = callback

    def show_notification(self, message_id, text, date):
        """
        Добавить уведомление в очередь

        Args:
            message_id: ID сообщения
            text: Текст сообщения
            date: Дата сообщения
        """
        self.notification_queue.put({
            'message_id': message_id,
            'text': text,
            'date': date
        })

        # Если окно еще не создано, создать его
        if not self.is_running:
            threading.Thread(target=self._start_ui, daemon=True).start()

    def _start_ui(self):
        """Запустить UI в отдельном потоке"""
        self.is_running = True
        self.root = tk.Tk()
        self._create_window()
        self._check_queue()
        self.root.mainloop()

    def _create_window(self):
        """Создать окно уведомления"""
        self.root.title("⚠️ ОБЯЗАТЕЛЬНОЕ УВЕДОМЛЕНИЕ")

        # Размер окна
        window_width = 700
        window_height = 500

        # Получить размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Вычислить позицию (по центру)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg="#1a1a1a")

        # ВАЖНО: Сделать окно всегда поверх других
        self.root.attributes('-topmost', True)

        # Отключить кнопку закрытия
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        # Заголовок
        header_frame = tk.Frame(self.root, bg="#ff5722", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="⚠️ ВАЖНОЕ СООБЩЕНИЕ ИЗ TELEGRAM",
            font=("Helvetica", 20, "bold"),
            fg="#ffffff",
            bg="#ff5722"
        )
        title_label.pack(expand=True)

        subtitle_label = tk.Label(
            header_frame,
            text="Подтвердите прочтение для продолжения работы",
            font=("Helvetica", 11),
            fg="#ffccbc",
            bg="#ff5722"
        )
        subtitle_label.pack()

        # Информационная панель
        info_frame = tk.Frame(self.root, bg="#1a1a1a")
        info_frame.pack(fill=tk.X, pady=15)

        self.date_label = tk.Label(
            info_frame,
            text="",
            font=("Helvetica", 12),
            fg="#888888",
            bg="#1a1a1a"
        )
        self.date_label.pack()

        self.message_id_label = tk.Label(
            info_frame,
            text="",
            font=("Helvetica", 10),
            fg="#666666",
            bg="#1a1a1a"
        )
        self.message_id_label.pack()

        # Контейнер для текста сообщения
        message_container = tk.Frame(self.root, bg="#1a1a1a")
        message_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(
            message_container,
            text="📨 Текст сообщения:",
            font=("Helvetica", 14, "bold"),
            fg="#ffffff",
            bg="#1a1a1a"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Текстовое поле с сообщением
        self.message_text = scrolledtext.ScrolledText(
            message_container,
            font=("Helvetica", 14),
            bg="#2a2a2a",
            fg="#ffffff",
            wrap=tk.WORD,
            relief=tk.FLAT,
            state=tk.DISABLED,
            padx=15,
            pady=15
        )
        self.message_text.pack(fill=tk.BOTH, expand=True)

        # Предупреждение
        warning_frame = tk.Frame(self.root, bg="#ff9800", height=60)
        warning_frame.pack(fill=tk.X, pady=(10, 0))
        warning_frame.pack_propagate(False)

        tk.Label(
            warning_frame,
            text="⚠️ Это окно нельзя закрыть без подтверждения прочтения!",
            font=("Helvetica", 12, "bold"),
            fg="#000000",
            bg="#ff9800"
        ).pack(expand=True)

        # Кнопка подтверждения
        button_frame = tk.Frame(self.root, bg="#1a1a1a")
        button_frame.pack(fill=tk.X, pady=20)

        self.confirm_btn = tk.Button(
            button_frame,
            text="✅ Я ПРОЧИТАЛ(А) ЭТО СООБЩЕНИЕ",
            font=("Helvetica", 14, "bold"),
            bg="#4caf50",
            fg="#ffffff",
            width=40,
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_confirm,
            activebackground="#45a049"
        )
        self.confirm_btn.pack()

        # Счетчик нажатий (требуется 2 нажатия для подтверждения)
        self.confirm_count = 0

        # Горячая клавиша
        self.root.bind("<Return>", lambda e: self._on_confirm())
        self.root.bind("<space>", lambda e: self._on_confirm())

        # Скрыть окно до получения первого сообщения
        self.root.withdraw()

    def _check_queue(self):
        """Проверить очередь сообщений"""
        try:
            # Если текущее сообщение не обработано, не показывать новое
            if self.current_message is None:
                message = self.notification_queue.get_nowait()
                self._display_message(message)
        except queue.Empty:
            pass

        # Проверять очередь каждые 500ms
        if self.root:
            self.root.after(500, self._check_queue)

    def _display_message(self, message):
        """Показать сообщение"""
        self.current_message = message
        self.confirm_count = 0

        # Обновить информацию
        self.date_label.config(text=f"📅 Дата: {message['date']}")
        self.message_id_label.config(text=f"ID: {message['message_id']}")

        # Обновить текст
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.insert(1.0, message['text'])
        self.message_text.config(state=tk.DISABLED)

        # Сбросить текст кнопки
        self.confirm_btn.config(
            text="✅ Я ПРОЧИТАЛ(А) ЭТО СООБЩЕНИЕ",
            bg="#4caf50"
        )

        # Показать окно
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

        # Включить звуковой сигнал (если доступен)
        try:
            self.root.bell()
        except:
            pass

        print(f"📢 Показано обязательное уведомление: {message['message_id']}")

    def _on_confirm(self):
        """Обработка подтверждения прочтения"""
        self.confirm_count += 1

        if self.confirm_count == 1:
            # Первое нажатие - предупреждение
            self.confirm_btn.config(
                text="⚠️ НАЖМИТЕ ЕЩЕ РАЗ ДЛЯ ПОДТВЕРЖДЕНИЯ",
                bg="#ff9800"
            )
        else:
            # Второе нажатие - подтверждение
            if self.current_message and self.on_confirm_callback:
                message_id = self.current_message['message_id']
                self.on_confirm_callback(message_id)

            print(f"✅ Подтверждено прочтение сообщения: {self.current_message['message_id']}")

            # Скрыть окно
            self.root.withdraw()
            self.current_message = None

    def _on_close_attempt(self):
        """Попытка закрыть окно (заблокирована)"""
        # Анимация предупреждения
        self.root.configure(bg="#ff0000")
        self.root.after(100, lambda: self.root.configure(bg="#1a1a1a"))

        # Звуковой сигнал
        try:
            self.root.bell()
        except:
            pass

        print("⚠️ Попытка закрыть окно заблокирована!")


class NotificationManager:
    """Менеджер для управления уведомлениями"""

    def __init__(self):
        self.notification = MandatoryNotification()

    def start(self, on_confirm_callback):
        """
        Запустить систему уведомлений

        Args:
            on_confirm_callback: Функция, которая будет вызываться при подтверждении
        """
        self.notification.set_confirm_callback(on_confirm_callback)

    def show(self, message_id, text, date):
        """Показать уведомление"""
        self.notification.show_notification(message_id, text, date)


# Тест (если запустить напрямую)
if __name__ == "__main__":
    def on_confirm(message_id):
        print(f"Пользователь подтвердил прочтение сообщения: {message_id}")

    manager = NotificationManager()
    manager.start(on_confirm)

    # Показать тестовое уведомление
    manager.show(
        12345,
        "Это тестовое сообщение для проверки системы обязательных уведомлений.\n\n"
        "Окно нельзя закрыть без подтверждения прочтения!\n\n"
        "Нажмите кнопку дважды для подтверждения.",
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # Второе уведомление через 5 секунд
    import time
    time.sleep(5)
    manager.show(
        67890,
        "Это второе тестовое сообщение!\n\nОно появится только после подтверждения первого.",
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
