import krpc
import time


class AutoShutdown:
    def __init__(self):
        # Подключаемся к KSP
        self.conn = krpc.connect(name="AutoShutdown")
        self.vessel = self.conn.space_center.active_vessel
        self.control = self.vessel.control

        print(f"Автоотключение для {self.vessel.name}")

    def monitor_touchdown(self):
        """Мониторинг физического касания с землей"""
        try:
            print("=== АВТООТКЛЮЧЕНИЕ ДВИГАТЕЛЯ АКТИВИРОВАНО ===")
            print("Ожидание физического касания с землей...")
            print("Для остановки нажмите Ctrl+C")

            shutdown_done = False
            was_flying = True

            while not shutdown_done:
                # Получаем текущую ситуацию корабля
                situation = self.vessel.situation.name
                throttle = self.control.throttle

                # Проверяем изменение состояния с "полета" на "касание"
                if (situation == "landed" or situation == "splashed") and was_flying:
                    if throttle > 0:
                        print(f"\n✓ ФИЗИЧЕСКОЕ КАСАНИЕ! Состояние: {situation}")
                        print("НЕМЕДЛЕННОЕ ОТКЛЮЧЕНИЕ ДВИГАТЕЛЯ!")
                        self.control.throttle = 0
                        shutdown_done = True
                        print("✓ Двигатель отключен")
                        break

                # Обновляем состояние для следующей проверки
                was_flying = (
                    situation == "flying"
                    or situation == "sub_orbital"
                    or situation == "orbiting"
                    or situation == "escaping"
                )

                # Статус
                altitude = self.vessel.flight().surface_altitude
                status = f"Состояние: {situation:12} | Высота: {altitude:5.1f}м | Тяга: {throttle:.1f}"
                print(status, end="\r")

                time.sleep(0.1)

            print("\nАвтоотключение завершено")

        except KeyboardInterrupt:
            print("\n=== МОНИТОРИНГ ОСТАНОВЛЕН ===")
        except Exception as e:
            print(f"\nОШИБКА: {e}")
            self.control.throttle = 0


# Запуск
if __name__ == "__main__":
    try:
        shutdown = AutoShutdown()
        shutdown.monitor_touchdown()
    except Exception as e:
        print(f"Ошибка: {e}")
