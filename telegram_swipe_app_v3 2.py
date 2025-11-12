import tkinter as tk
from tkinter import messagebox, scrolledtext
import json
import os
from datetime import datetime
import asyncio
import threading
from telegram_loader_v3 import load_messages_v3, TelegramMessageLoaderV3


class TelegramSwipeAppV3:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Message Swiper v3 - Умная версия")
        self.root.geometry("650x850")
        self.root.configure(bg="#1a1a1a")
        
        # Данные
        self.dialogs = []
        self.current_index = 0
        self.loader = None
        
        # Автообновление
        self.auto_refresh_enabled = False
        self.refresh_interval = 3600  # 1 час
        
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        # Верхняя панель
        header = tk.Frame(self.root, bg="#1a1a1a")
        header.pack(pady=15, fill=tk.X)
        
        title = tk.Label(header, text="📱 Telegram Swiper v3", 
                        font=("Helvetica", 24, "bold"), 
                        fg="#ffffff", bg="#1a1a1a")
        title.pack()
        
        subtitle = tk.Label(header, text="Умная версия - отслеживает каждое сообщение", 
                           font=("Helvetica", 11), 
                           fg="#888888", bg="#1a1a1a")
        subtitle.pack()
        
        # Информационная панель
        info_frame = tk.Frame(header, bg="#1a1a1a")
        info_frame.pack(pady=8)
        
        self.counter_label = tk.Label(info_frame, text="0 / 0", 
                                     font=("Helvetica", 14, "bold"), 
                                     fg="#888888", bg="#1a1a1a")
        self.counter_label.pack(side=tk.LEFT, padx=10)
        
        self.unread_label = tk.Label(info_frame, text="💬 Непрочитанных: 0", 
                                     font=("Helvetica", 12), 
                                     fg="#ff9800", bg="#1a1a1a")
        self.unread_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(header, text="⏸️ Ожидание загрузки", 
                                     font=("Helvetica", 11), 
                                     fg="#888888", bg="#1a1a1a")
        self.status_label.pack(pady=3)
        
        # Карточка диалога
        self.card_frame = tk.Frame(self.root, bg="#ffffff", 
                                  relief=tk.RAISED, borderwidth=2)
        self.card_frame.pack(pady=15, padx=30, fill=tk.BOTH, expand=True)
        
        # Заголовок
        self.dialog_header = tk.Frame(self.card_frame, bg="#f0f0f0")
        self.dialog_header.pack(fill=tk.X)
        
        self.client_label = tk.Label(self.dialog_header, text="",
                                    font=("Helvetica", 17, "bold"),
                                    bg="#f0f0f0", fg="#333333",
                                    pady=12)
        self.client_label.pack()
        
        self.date_label = tk.Label(self.dialog_header, text="",
                                  font=("Helvetica", 11),
                                  bg="#f0f0f0", fg="#666666",
                                  pady=5)
        self.date_label.pack()
        
        self.unread_info_label = tk.Label(self.dialog_header, text="",
                                         font=("Helvetica", 11, "bold"),
                                         bg="#f0f0f0", fg="#ff5722")
        self.unread_info_label.pack(pady=5)
        
        # Контекст
        context_container = tk.Frame(self.card_frame, bg="#ffffff")
        context_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(context_container, text="💬 История диалога:", 
                font=("Helvetica", 12, "bold"),
                bg="#ffffff", fg="#666666").pack(anchor=tk.W, pady=(0, 10))
        
        self.context_text = scrolledtext.ScrolledText(
            context_container,
            font=("Helvetica", 13),
            bg="#fafafa",
            fg="#000000",
            wrap=tk.WORD,
            relief=tk.FLAT,
            state=tk.DISABLED,
            height=12
        )
        self.context_text.pack(fill=tk.BOTH, expand=True)
        
        # Теги для стилизации
        self.context_text.tag_config("from_me", foreground="#0066cc", font=("Helvetica", 13, "bold"))
        self.context_text.tag_config("from_client", foreground="#cc0066", font=("Helvetica", 13, "bold"))
        self.context_text.tag_config("time", foreground="#999999", font=("Helvetica", 11))
        self.context_text.tag_config("message", foreground="#333333")
        self.context_text.tag_config("unread", background="#fff9c4", font=("Helvetica", 13, "bold"))
        self.context_text.tag_config("separator", foreground="#999999", font=("Helvetica", 11, "italic"))
        
        # Отдельная секция для непрочитанных
        unread_container = tk.Frame(self.card_frame, bg="#fff3e0")
        unread_container.pack(fill=tk.BOTH, padx=15, pady=(0, 15))
        
        tk.Label(unread_container, text="⚠️ Требуют ответа:", 
                font=("Helvetica", 12, "bold"),
                bg="#fff3e0", fg="#e65100").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.unread_text = scrolledtext.ScrolledText(
            unread_container,
            font=("Helvetica", 13),
            bg="#fffde7",
            fg="#000000",
            wrap=tk.WORD,
            relief=tk.FLAT,
            state=tk.DISABLED,
            height=6
        )
        self.unread_text.pack(fill=tk.BOTH, padx=10, pady=(0, 10))
        
        # Кнопки
        button_frame = tk.Frame(self.root, bg="#1a1a1a")
        button_frame.pack(pady=20)
        
        self.left_btn = tk.Button(button_frame, 
                                  text="👈\nНепрочитанное\n(вернется)",
                                  font=("Helvetica", 11, "bold"),
                                  bg="#ff9800", fg="#ffffff",
                                  width=15, height=4,
                                  relief=tk.FLAT,
                                  command=self.swipe_left,
                                  cursor="hand2")
        self.left_btn.pack(side=tk.LEFT, padx=12)
        
        self.right_btn = tk.Button(button_frame, 
                                   text="✅\nОбработано\n(убрать навсегда)",
                                   font=("Helvetica", 11, "bold"),
                                   bg="#4caf50", fg="#ffffff",
                                   width=15, height=4,
                                   relief=tk.FLAT,
                                   command=self.swipe_right,
                                   cursor="hand2")
        self.right_btn.pack(side=tk.LEFT, padx=12)
        
        # Меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="⚙️  Настроить Telegram", command=self.setup_telegram)
        file_menu.add_command(label="🔄 Загрузить сообщения", command=self.load_messages_thread)
        file_menu.add_separator()
        file_menu.add_checkbutton(label="⏰ Автообновление (1 час)", 
                                  command=self.toggle_auto_refresh)
        file_menu.add_separator()
        file_menu.add_command(label="📊 Подробная статистика", command=self.show_stats)
        file_menu.add_command(label="🗑️  Очистить всю историю", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="ℹ️  О приложении", command=self.show_about)
        file_menu.add_command(label="❌ Выход", command=self.root.quit)
        
        # Горячие клавиши
        self.root.bind("<Left>", lambda e: self.swipe_left())
        self.root.bind("<Right>", lambda e: self.swipe_right())
        self.root.bind("<space>", lambda e: self.swipe_right())
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
    def update_display(self):
        """Обновить отображение текущего диалога"""
        if not self.dialogs or self.current_index >= len(self.dialogs):
            self.show_completion()
            return
            
        dialog = self.dialogs[self.current_index]
        
        # Счетчик
        self.counter_label.config(
            text=f"{self.current_index + 1} / {len(self.dialogs)}"
        )
        
        # Количество непрочитанных в этом диалоге
        unread_count = dialog['unread_count']
        self.unread_label.config(
            text=f"💬 Непрочитанных: {unread_count}"
        )
        
        # Имя
        self.client_label.config(text=f"👤 {dialog['dialog_name']}")
        
        # Дата
        date_text = f"📅 Последнее сообщение: {dialog['last_message_date']}"
        if dialog.get('last_your_message_date'):
            date_text += f"\n✉️  Вы писали: {dialog['last_your_message_date']}"
        self.date_label.config(text=date_text)
        
        # Информация о непрочитанных
        self.unread_info_label.config(
            text=f"⚠️ {unread_count} сообщений требуют ответа!"
        )
        
        # Контекст диалога
        self.display_context(dialog)
        
        # Непрочитанные сообщения отдельно
        self.display_unread_messages(dialog)
        
    def display_context(self, dialog):
        """Показать контекст диалога"""
        self.context_text.config(state=tk.NORMAL)
        self.context_text.delete(1.0, tk.END)
        
        if 'context' in dialog and dialog['context']:
            for msg in dialog['context']:
                sender_tag = "from_me" if msg['from_me'] else "from_client"
                arrow = "→" if msg['from_me'] else "←"
                
                self.context_text.insert(tk.END, f"{arrow} ", sender_tag)
                self.context_text.insert(tk.END, f"[{msg['date']}] ", "time")
                self.context_text.insert(tk.END, f"{msg['sender']}:\n", sender_tag)
                self.context_text.insert(tk.END, f"{msg['text']}\n\n", "message")
        
        self.context_text.config(state=tk.DISABLED)
        
    def display_unread_messages(self, dialog):
        """Показать непрочитанные сообщения отдельно"""
        self.unread_text.config(state=tk.NORMAL)
        self.unread_text.delete(1.0, tk.END)
        
        if dialog['unread_messages']:
            for i, msg in enumerate(dialog['unread_messages'], 1):
                self.unread_text.insert(tk.END, f"{i}. ", "unread")
                self.unread_text.insert(tk.END, f"[{msg['time']}] ", "time")
                self.unread_text.insert(tk.END, f"{msg['text']}\n\n", "unread")
        
        self.unread_text.config(state=tk.DISABLED)
        
    def swipe_left(self):
        """Пометить непрочитанным - вернется при следующем сканировании"""
        if self.current_index >= len(self.dialogs):
            return
            
        dialog = self.dialogs[self.current_index]
        
        if self.loader:
            # Помечаем ВСЕ непрочитанные сообщения как "mark_unread"
            message_ids = [msg['id'] for msg in dialog['unread_messages']]
            self.loader.mark_messages_as_processed(
                dialog['dialog_id'],
                message_ids,
                action="mark_unread"
            )
            
            # Помечаем в Telegram
            asyncio.run(self.loader.mark_dialog_as_unread(dialog['dialog_id']))
        
        self.animate_swipe("left")
        self.current_index += 1
        self.root.after(250, self.update_display)
        
    def swipe_right(self):
        """Обработано - больше не показывать"""
        if self.current_index >= len(self.dialogs):
            return
            
        dialog = self.dialogs[self.current_index]
        
        if self.loader:
            # Помечаем ВСЕ непрочитанные сообщения как "answered"
            message_ids = [msg['id'] for msg in dialog['unread_messages']]
            self.loader.mark_messages_as_processed(
                dialog['dialog_id'],
                message_ids,
                action="answered"
            )
        
        self.animate_swipe("right")
        self.current_index += 1
        self.root.after(250, self.update_display)
        
    def animate_swipe(self, direction):
        """Анимация свайпа"""
        if direction == "left":
            self.card_frame.configure(bg="#ffe0b2")
        else:
            self.card_frame.configure(bg="#c8e6c9")
            
        self.root.after(200, lambda: self.card_frame.configure(bg="#ffffff"))
        
    def show_completion(self):
        """Экран завершения"""
        self.client_label.config(text="🎉 Все диалоги обработаны!")
        self.date_label.config(text="")
        self.unread_info_label.config(text="")
        
        self.context_text.config(state=tk.NORMAL)
        self.context_text.delete(1.0, tk.END)
        self.context_text.insert(1.0, 
            f"✅ Обработано {len(self.dialogs)} диалогов\n\n"
            f"Все сообщения проверены!\n\n"
            f"{'Следующее автообновление через ' + str(self.refresh_interval // 60) + ' минут' if self.auto_refresh_enabled else 'Автообновление выключено'}")
        self.context_text.config(state=tk.DISABLED)
        
        self.unread_text.config(state=tk.NORMAL)
        self.unread_text.delete(1.0, tk.END)
        self.unread_text.insert(1.0, "Нет непрочитанных сообщений")
        self.unread_text.config(state=tk.DISABLED)
        
        self.left_btn.config(state=tk.DISABLED)
        self.right_btn.config(state=tk.DISABLED)
        
    def setup_telegram(self):
        """Настройка Telegram API"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройка Telegram")
        dialog.geometry("500x280")
        dialog.configure(bg="#ffffff")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="API ID:", 
                font=("Helvetica", 12), bg="#ffffff").pack(pady=(20, 5))
        api_id_entry = tk.Entry(dialog, width=45, font=("Helvetica", 12))
        api_id_entry.pack(pady=5)
        
        tk.Label(dialog, text="API Hash:", 
                font=("Helvetica", 12), bg="#ffffff").pack(pady=5)
        api_hash_entry = tk.Entry(dialog, width=45, font=("Helvetica", 12))
        api_hash_entry.pack(pady=5)
        
        # Загрузка настроек
        if os.path.exists("telegram_config_v3.json"):
            try:
                with open("telegram_config_v3.json", "r") as f:
                    config = json.load(f)
                    api_id_entry.insert(0, config.get("api_id", ""))
                    api_hash_entry.insert(0, config.get("api_hash", ""))
            except:
                pass
        
        def save_config():
            config = {
                "api_id": api_id_entry.get().strip(),
                "api_hash": api_hash_entry.get().strip()
            }
            
            if not config["api_id"] or not config["api_hash"]:
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            
            with open("telegram_config_v3.json", "w") as f:
                json.dump(config, f)
            
            messagebox.showinfo("Успех", "Настройки сохранены!")
            dialog.destroy()
            
        tk.Button(dialog, text="💾 Сохранить", command=save_config,
                 bg="#4caf50", fg="#ffffff", 
                 font=("Helvetica", 12, "bold"),
                 padx=40, pady=12).pack(pady=25)
        
    def load_config(self):
        """Загрузить конфигурацию"""
        if os.path.exists("telegram_config_v3.json"):
            try:
                with open("telegram_config_v3.json", "r") as f:
                    return json.load(f)
            except:
                return None
        return None
        
    def load_messages_thread(self):
        """Загрузить в потоке"""
        thread = threading.Thread(target=self.load_messages, daemon=True)
        thread.start()
        
    def load_messages(self):
        """Загрузить сообщения"""
        config = self.load_config()
        
        if not config:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", 
                "Сначала настройте Telegram:\nФайл → Настроить Telegram"
            ))
            return
        
        self.root.after(0, lambda: self.status_label.config(
            text="⏳ Умное сканирование...", fg="#ff9800"
        ))
        
        try:
            dialogs, loader = asyncio.run(load_messages_v3(
                config["api_id"],
                config["api_hash"],
                hours_back=24
            ))
            
            self.dialogs = dialogs
            self.loader = loader
            self.current_index = 0
            
            total_unread = sum(d['unread_count'] for d in dialogs)
            
            self.root.after(0, self.update_display)
            self.root.after(0, lambda: self.status_label.config(
                text=f"✅ {len(dialogs)} диалогов | {total_unread} непрочитанных", 
                fg="#4caf50"
            ))
            
            self.root.after(0, lambda: self.left_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.right_btn.config(state=tk.NORMAL))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", 
                f"Не удалось загрузить:\n{str(e)}"
            ))
            self.root.after(0, lambda: self.status_label.config(
                text="❌ Ошибка загрузки", fg="#f44336"
            ))
            
    def toggle_auto_refresh(self):
        """Переключить автообновление"""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        
        if self.auto_refresh_enabled:
            messagebox.showinfo(
                "Автообновление v3", 
                f"Умное автообновление включено!\n\n"
                f"Обновление каждые {self.refresh_interval // 60} минут\n"
                f"Отслеживает каждое сообщение отдельно"
            )
            self.schedule_refresh()
        else:
            messagebox.showinfo("Автообновление", "Автообновление выключено")
            
    def schedule_refresh(self):
        """Запланировать обновление"""
        if self.auto_refresh_enabled:
            self.load_messages_thread()
            self.root.after(self.refresh_interval * 1000, self.schedule_refresh)
            
    def show_stats(self):
        """Показать статистику"""
        if not self.loader:
            messagebox.showinfo("Статистика", "Сначала загрузите сообщения")
            return
            
        stats = self.loader.get_statistics()
        last_scan = self.loader.get_last_scan_time()
        
        stats_text = f"""
📊 Подробная статистика v3:

✅ Обработано сообщений: {stats['total_answered']}
👈 Помечено непрочитанными: {stats['total_marked']}
💬 Уникальных диалогов: {stats['unique_dialogs']}
🔄 Всего сканирований: {stats['total_scans']}

⏰ Последнее сканирование:
   {last_scan['time'] if last_scan else 'Нет данных'}
   Найдено диалогов: {last_scan['messages_found'] if last_scan else 0}
   Просканировано: {last_scan['dialogs_scanned'] if last_scan else 0}

📋 Текущая сессия:
   Загружено: {len(self.dialogs)}
   Обработано: {self.current_index}
   Осталось: {len(self.dialogs) - self.current_index}

💡 Преимущество v3:
   Отслеживает каждое сообщение отдельно!
   Если клиент написал новое - покажет снова.
        """
        
        messagebox.showinfo("Статистика v3", stats_text)
        
    def clear_history(self):
        """Очистить историю"""
        result = messagebox.askyesno(
            "Очистить всю историю?",
            "Это удалит ВСЕ данные об обработанных сообщениях.\n\n"
            "ВСЕ диалоги покажутся заново!\n\n"
            "Продолжить?"
        )
        
        if result and self.loader:
            import sqlite3
            conn = sqlite3.connect(self.loader.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM processed_messages')
            cursor.execute('DELETE FROM dialog_tracking')
            cursor.execute('DELETE FROM scan_history')
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", "Вся история очищена!")
            
    def show_about(self):
        """О приложении"""
        about_text = """
🎯 Telegram Message Swiper v3
Умная версия

✨ Особенности v3:
• Отслеживает КАЖДОЕ сообщение отдельно
• Если клиент написал новое - покажет снова
• Показывает сколько непрочитанных в диалоге
• Умное сканирование всех сообщений
• Детальная статистика

👉 Свайп вправо = Обработано (все сообщения)
👈 Свайп влево = Пометить непрочитанным

⌨️ Горячие клавиши:
→ = Обработано
← = Непрочитанное  
Space = Обработано
Esc = Выход

Версия 3.0
        """
        messagebox.showinfo("О приложении", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramSwipeAppV3(root)
    root.mainloop()
