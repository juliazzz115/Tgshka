"""
Модуль для мониторинга Telegram канала и получения новых сообщений
"""
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
from datetime import datetime
import json
import os
import sqlite3


class TelegramChannelMonitor:
    def __init__(self, api_id, api_hash, session_name="channel_monitor"):
        """
        Инициализация монитора канала

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_name: Имя сессии для хранения авторизации
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self.channel_id = None
        self.db_path = "notifications.db"
        self.message_callback = None

        # Инициализация БД
        self._init_database()

    def _init_database(self):
        """Инициализация базы данных для хранения обработанных сообщений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                text TEXT,
                date TEXT,
                confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    async def connect(self):
        """Подключение к Telegram"""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        print("✅ Успешно подключено к Telegram")

    async def get_channels(self):
        """Получить список доступных каналов"""
        dialogs = await self.client.get_dialogs()
        channels = []

        for dialog in dialogs:
            if dialog.is_channel:
                channels.append({
                    'id': dialog.id,
                    'name': dialog.name,
                    'username': dialog.entity.username if hasattr(dialog.entity, 'username') else None
                })

        return channels

    def set_channel(self, channel_id):
        """Установить канал для мониторинга"""
        self.channel_id = channel_id
        print(f"📺 Установлен канал для мониторинга: {channel_id}")

    def set_message_callback(self, callback):
        """
        Установить callback для обработки новых сообщений

        Args:
            callback: Функция, которая будет вызываться при получении нового сообщения
                     Должна принимать параметры: message_id, text, date
        """
        self.message_callback = callback

    def is_message_processed(self, message_id):
        """Проверить, было ли сообщение уже обработано"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT confirmed FROM processed_messages WHERE message_id = ?',
            (message_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == 1:
            return True
        return False

    def save_message(self, message_id, channel_id, text, date):
        """Сохранить сообщение в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO processed_messages
            (message_id, channel_id, text, date, confirmed)
            VALUES (?, ?, ?, ?, 0)
        ''', (message_id, channel_id, text, date))

        conn.commit()
        conn.close()

    def mark_message_confirmed(self, message_id):
        """Пометить сообщение как подтвержденное"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE processed_messages SET confirmed = 1 WHERE message_id = ?',
            (message_id,)
        )

        conn.commit()
        conn.close()
        print(f"✅ Сообщение {message_id} помечено как прочитанное")

    def get_unconfirmed_messages(self):
        """Получить все неподтвержденные сообщения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT message_id, text, date
            FROM processed_messages
            WHERE confirmed = 0
            ORDER BY date DESC
        ''')

        messages = []
        for row in cursor.fetchall():
            messages.append({
                'message_id': row[0],
                'text': row[1],
                'date': row[2]
            })

        conn.close()
        return messages

    async def check_new_messages(self):
        """
        Проверить новые сообщения в канале (за последние 24 часа)
        Возвращает список новых непрочитанных сообщений
        """
        if not self.channel_id:
            raise ValueError("Канал не установлен. Используйте set_channel()")

        messages = await self.client.get_messages(self.channel_id, limit=50)
        new_messages = []

        for msg in messages:
            if msg.text and not self.is_message_processed(msg.id):
                message_data = {
                    'message_id': msg.id,
                    'text': msg.text,
                    'date': msg.date.strftime('%Y-%m-%d %H:%M:%S')
                }

                # Сохранить в БД
                self.save_message(
                    msg.id,
                    self.channel_id,
                    msg.text,
                    message_data['date']
                )

                new_messages.append(message_data)

        return new_messages

    async def start_monitoring(self, check_interval=1800):
        """
        Запустить мониторинг канала (проверка каждые 30 минут по умолчанию)

        Args:
            check_interval: Интервал проверки в секундах (по умолчанию 1800 = 30 минут)
        """
        if not self.channel_id:
            raise ValueError("Канал не установлен. Используйте set_channel()")

        print(f"🔄 Запуск мониторинга канала (проверка каждые {check_interval//60} минут)...")

        while True:
            try:
                new_messages = await self.check_new_messages()

                if new_messages:
                    print(f"📨 Найдено {len(new_messages)} новых сообщений")

                    # Вызвать callback для каждого нового сообщения
                    if self.message_callback:
                        for msg in new_messages:
                            self.message_callback(
                                msg['message_id'],
                                msg['text'],
                                msg['date']
                            )
                else:
                    print("✅ Новых сообщений нет")

                # Ждать до следующей проверки
                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"❌ Ошибка при проверке сообщений: {e}")
                await asyncio.sleep(60)  # Подождать минуту при ошибке

    async def disconnect(self):
        """Отключиться от Telegram"""
        if self.client:
            await self.client.disconnect()
            print("👋 Отключено от Telegram")


# Функции для работы с конфигурацией
def save_config(api_id, api_hash, channel_id):
    """Сохранить конфигурацию"""
    config = {
        'api_id': api_id,
        'api_hash': api_hash,
        'channel_id': channel_id
    }

    with open('telegram_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("✅ Конфигурация сохранена")


def load_config():
    """Загрузить конфигурацию"""
    if not os.path.exists('telegram_config.json'):
        return None

    with open('telegram_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)
