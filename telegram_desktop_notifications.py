#!/usr/bin/env python3
"""
Система обязательных desktop уведомлений из Telegram канала
Автор: Claude AI
Версия: 1.0

Функционал:
- Мониторинг Telegram канала (проверка каждые 30 минут)
- Обязательные desktop уведомления (нельзя закрыть без подтверждения)
- Отслеживание прочитанных сообщений
- Очередь уведомлений
"""

import asyncio
import sys
from telegram_channel_monitor import TelegramChannelMonitor, load_config, save_config
from mandatory_notification import NotificationManager


class TelegramDesktopNotifications:
    """Главный класс приложения"""

    def __init__(self):
        self.monitor = None
        self.notification_manager = NotificationManager()
        self.config = None

    def setup(self):
        """Первичная настройка приложения"""
        print("=" * 70)
        print("🔔 СИСТЕМА ОБЯЗАТЕЛЬНЫХ TELEGRAM УВЕДОМЛЕНИЙ")
        print("=" * 70)
        print()

        # Попытаться загрузить существующую конфигурацию
        self.config = load_config()

        if self.config:
            print("✅ Найдена существующая конфигурация")
            print(f"   API ID: {self.config['api_id']}")
            print(f"   Channel ID: {self.config.get('channel_id', 'Не установлен')}")
            print()

            response = input("Использовать существующую конфигурацию? (y/n): ")
            if response.lower() != 'y':
                self.config = None

        # Если конфигурации нет, создать новую
        if not self.config:
            print()
            print("📝 Настройка Telegram API")
            print("-" * 70)
            print()
            print("Для работы с Telegram API нужно получить credentials:")
            print("1. Перейдите на https://my.telegram.org")
            print("2. Войдите с помощью номера телефона")
            print("3. Перейдите в 'API development tools'")
            print("4. Создайте новое приложение")
            print("5. Скопируйте API ID и API Hash")
            print()

            api_id = input("Введите API ID: ").strip()
            api_hash = input("Введите API Hash: ").strip()

            self.config = {
                'api_id': api_id,
                'api_hash': api_hash,
                'channel_id': None
            }

        # Создать монитор
        self.monitor = TelegramChannelMonitor(
            self.config['api_id'],
            self.config['api_hash']
        )

    async def select_channel(self):
        """Выбрать канал для мониторинга"""
        print()
        print("📺 Подключение к Telegram...")

        await self.monitor.connect()

        print()
        print("📋 Получение списка каналов...")

        channels = await self.monitor.get_channels()

        if not channels:
            print("❌ Не найдено доступных каналов!")
            sys.exit(1)

        print()
        print("Доступные каналы:")
        print("-" * 70)

        for i, channel in enumerate(channels, 1):
            username = f"@{channel['username']}" if channel['username'] else ""
            print(f"{i}. {channel['name']} {username} (ID: {channel['id']})")

        print()

        while True:
            try:
                choice = input(f"Выберите канал (1-{len(channels)}): ").strip()
                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(channels):
                    selected_channel = channels[choice_idx]
                    self.monitor.set_channel(selected_channel['id'])
                    self.config['channel_id'] = selected_channel['id']

                    # Сохранить конфигурацию
                    save_config(
                        self.config['api_id'],
                        self.config['api_hash'],
                        self.config['channel_id']
                    )

                    print()
                    print(f"✅ Выбран канал: {selected_channel['name']}")
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте снова.")

            except ValueError:
                print("❌ Введите число!")
            except KeyboardInterrupt:
                print("\n\n👋 Отменено пользователем")
                sys.exit(0)

    def on_new_message(self, message_id, text, date):
        """Callback для обработки новых сообщений"""
        print(f"\n📨 Новое сообщение!")
        print(f"   ID: {message_id}")
        print(f"   Дата: {date}")
        print(f"   Текст: {text[:100]}...")
        print()

        # Показать обязательное уведомление
        self.notification_manager.show(message_id, text, date)

    def on_confirm_read(self, message_id):
        """Callback для подтверждения прочтения"""
        print(f"\n✅ Пользователь подтвердил прочтение сообщения: {message_id}")

        # Пометить в БД как прочитанное
        self.monitor.mark_message_confirmed(message_id)

    async def check_unconfirmed_messages(self):
        """Проверить и показать неподтвержденные сообщения"""
        unconfirmed = self.monitor.get_unconfirmed_messages()

        if unconfirmed:
            print()
            print(f"⚠️ Найдено {len(unconfirmed)} неподтвержденных сообщений!")
            print()

            for msg in unconfirmed:
                self.notification_manager.show(
                    msg['message_id'],
                    msg['text'],
                    msg['date']
                )

    async def run(self):
        """Запустить приложение"""
        # Настройка
        self.setup()

        # Если канал не установлен, выбрать его
        if not self.config.get('channel_id'):
            await self.select_channel()
        else:
            await self.monitor.connect()
            self.monitor.set_channel(self.config['channel_id'])

        # Установить callbacks
        self.monitor.set_message_callback(self.on_new_message)
        self.notification_manager.start(self.on_confirm_read)

        # Проверить неподтвержденные сообщения
        await self.check_unconfirmed_messages()

        print()
        print("=" * 70)
        print("🚀 СИСТЕМА ЗАПУЩЕНА")
        print("=" * 70)
        print()
        print("Параметры:")
        print(f"  • Проверка новых сообщений: каждые 30 минут")
        print(f"  • Канал: {self.config['channel_id']}")
        print(f"  • База данных: {self.monitor.db_path}")
        print()
        print("ℹ️  Для остановки нажмите Ctrl+C")
        print()
        print("-" * 70)
        print()

        # Запустить мониторинг
        try:
            await self.monitor.start_monitoring(check_interval=1800)  # 30 минут
        except KeyboardInterrupt:
            print("\n\n🛑 Остановка приложения...")
            await self.monitor.disconnect()
            print("👋 До свидания!")


def main():
    """Точка входа в приложение"""
    try:
        app = TelegramDesktopNotifications()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n\n👋 Приложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
