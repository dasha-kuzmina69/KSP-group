import krpc
import time
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

print(" ПОДКЛЮЧЕНИЕ К KSP...")
conn = krpc.connect(name="KSP_Telemetry")
vessel = conn.space_center.active_vessel

# Параметры
TARGET_ALTITUDE = 40000
MAX_TIME = 140
TURN_START = 800
TURN_END = 25000

# Массивы данных
times = []
altitudes = []
speeds = []
thrusts = []

print("1. ЗАПУСК ДВИГАТЕЛЕЙ...")
vessel.control.gear = False
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.control.throttle = 1.0
vessel.control.activate_next_stage()

start_time = time.time()
print_time = start_time

print("2. СБОР ТЕЛЕМЕТРИИ...")
print("Время(с)  Высота(м)  Скорость(м/с)")
print("-" * 40)

try:
    while vessel.flight().mean_altitude < TARGET_ALTITUDE:
        current_time = time.time() - start_time

        # Логирование каждые 5 секунд
        if time.time() - print_time > 5:
            speed_orbit = vessel.orbit.speed
            print(
                f"{current_time:6.1f}с  {vessel.flight().mean_altitude:8.0f}м  {speed_orbit:10.1f}м/с"
            )
            print_time = time.time()

        if current_time > MAX_TIME:
            print(f"Достигнуто {MAX_TIME} секунд")
            break

        # Автопилот
        altitude = vessel.flight().mean_altitude
        h_speed = vessel.flight().horizontal_speed

        if TURN_START < altitude < TURN_END:
            turn_angle = ((altitude - TURN_START) / (TURN_END - TURN_START)) * 80
            vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)

        if altitude > 30000 and h_speed > 800:
            vessel.auto_pilot.target_pitch_and_heading(5, 90)

        times.append(current_time)
        altitudes.append(altitude)
        speeds.append(vessel.orbit.speed)
        thrusts.append(vessel.thrust)

        # Отделение ступеней
        if vessel.thrust == 0 and vessel.control.current_stage > 1:
            print(f"Отделение ступени на {current_time:.1f}с")
            vessel.control.activate_next_stage()
            time.sleep(1)

        time.sleep(0.05)

except Exception as e:
    print(f"Ошибка: {e}")
    import traceback

    traceback.print_exc()

print(f"\n3. ПОЛЕТ ЗАВЕРШЕН. Собрано {len(times)} точек")
vessel.auto_pilot.disengage()

# Конвертируем в numpy массивы
times = np.array(times)
altitudes = np.array(altitudes)
speeds = np.array(speeds)
thrusts = np.array(thrusts)

# Проверяем данные
if len(times) == 0:
    print("ОШИБКА: Нет данных!")
    exit()

print(f"\nСТАТИСТИКА ДАННЫХ:")
print(f"- Записей: {len(times)}")
print(f"- Время полета: {times[-1]:.1f} с")
print(f"- Высота: от {altitudes[0]:.0f} до {altitudes[-1]:.0f} м")
print(f"- Скорость: от {speeds[0]:.1f} до {speeds[-1]:.1f} м/с")
print(f"- Максимальная скорость: {np.max(speeds):.1f} м/с")

# ============================================================================
# ГРАФИК: v(h) - СКОРОСТЬ ОТ ВЫСОТЫ (ЕДИНСТВЕННЫЙ)
# ============================================================================

plt.figure(figsize=(10, 6))

# Создаем папку для графиков
os.makedirs("ksp_graphs", exist_ok=True)

# Основной график - скорость от высоты
plt.plot(speeds, altitudes / 1000, "b-", linewidth=3)

# Настройка осей и сетки
plt.xlabel("Скорость, м/с", fontsize=14)
plt.ylabel("Высота, км", fontsize=14)
plt.title(
    "Зависимость скорости от высоты\n(Экспериментальные данные KSP)",
    fontsize=16,
    fontweight="bold",
)

plt.xlim(0, 1200)
plt.ylim(0, 70)

plt.xticks([0, 200, 400, 600, 800, 1000, 1200])
plt.yticks([0, 10, 20, 30, 40, 50, 60, 70])
plt.grid(True, linestyle="--", alpha=0.7)

for x in [200, 400, 600, 800, 1000]:
    plt.axvline(x=x, color="gray", linestyle=":", alpha=0.5)

# Горизонтальные линии
for y in [10, 20, 30, 40, 50, 60]:
    plt.axhline(y=y, color="gray", linestyle=":", alpha=0.5)

# Добавляем информацию о максимальной скорости
max_speed = np.max(speeds)
max_speed_idx = np.argmax(speeds)
max_speed_altitude = altitudes[max_speed_idx] / 1000

plt.plot(
    max_speed,
    max_speed_altitude,
    "ro",
    markersize=8,
    label=f"Макс. скорость: {max_speed:.0f} м/с",
)
plt.annotate(
    f"Макс. скорость\n{max_speed:.0f} м/с\nна {max_speed_altitude:.1f} км",
    xy=(max_speed, max_speed_altitude),
    xytext=(max_speed - 200, max_speed_altitude + 5),
    fontsize=10,
    color="red",
    arrowprops=dict(arrowstyle="->", color="red", alpha=0.7),
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
)

plt.legend(loc="lower right", fontsize=10)
plt.tight_layout()

# Сохраняем график
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"ksp_graphs/speed_vs_height_{timestamp}.png"
plt.savefig(filename, dpi=300, bbox_inches="tight")
print(f"\n✓ ГРАФИК СОХРАНЕН: {filename}")

# ============================================================================
# ВЫВОД РЕЗУЛЬТАТОВ ДЛЯ СРАВНЕНИЯ
# ============================================================================

print("\n" + "=" * 60)
print("ДАННЫЕ ДЛЯ СРАВНЕНИЯ С ТЕОРЕТИЧЕСКИМ ГРАФИКОМ:")
print("=" * 60)

if len(speeds) > 0:
    # Выводим скорость на разных высотах
    height_points = [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]

    for h in height_points:
        if h <= np.max(altitudes):
            # Находим ближайшую точку к заданной высоте
            idx = np.argmin(np.abs(altitudes - h))
            print(
                f"На {h/1000:5.1f} км: v = {speeds[idx]:6.1f} м/с (t = {times[idx]:5.1f} с)"
            )

print("\n" + "=" * 60)
print("Готово! График зависимости скорости от высоты построен.")
print("Теперь можно сравнить с теоретическим графиком.")
print("=" * 60)

# Показываем график
plt.show()
