import krpc
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

print("🚀 ПОДКЛЮЧЕНИЕ К KSP...")
conn = krpc.connect(name="KSP_Telemetry")
vessel = conn.space_center.active_vessel

# Параметры
TARGET_ALTITUDE = 450000
MAX_TIME = 150
TURN_START = 800
TURN_END = 25000

# Массивы данных
times = []
speeds = []  # Глобальная скорость
altitudes = []  # Высота
thrusts = []  # Тяга

print("1. ЗАПУСК ДВИГАТЕЛЕЙ...")
vessel.control.gear = False
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)
vessel.control.throttle = 1.0
vessel.control.activate_next_stage()

start_time = time.time()

print("\n2. СБОР ТЕЛЕМЕТРИИ...")
print("Время(с)  Высота(м)  Скорость(м/с)  Тяга(кН)")
print("-" * 60)

try:
    # Летим до 150 секунд или достижения целевой высоты
    while (
        time.time() - start_time
    ) < 150 and vessel.flight().mean_altitude < TARGET_ALTITUDE:
        current_time = time.time() - start_time

        if current_time > MAX_TIME:
            print(f"\nДостигнуто максимальное время ({MAX_TIME} секунд)")
            break

        # Получаем скорость - ГЛОБАЛЬНУЮ скорость (орбитальную)
        current_speed = vessel.orbit.speed

        # Автопилот
        altitude = vessel.flight().mean_altitude
        h_speed = vessel.flight().horizontal_speed

        if TURN_START < altitude < TURN_END:
            turn_angle = ((altitude - TURN_START) / (TURN_END - TURN_START)) * 80
            vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)

        if altitude > 30000 and h_speed > 800:
            vessel.auto_pilot.target_pitch_and_heading(5, 90)

        # Сбор данных
        times.append(current_time)
        speeds.append(current_speed)
        altitudes.append(altitude)
        thrusts.append(vessel.thrust)

        # Логирование каждые 10 секунд
        if int(current_time) % 10 == 0 and current_time - int(current_time) < 0.1:
            thrust_kn = vessel.thrust / 1000
            print(
                f"{current_time:6.1f}с  {altitude:8.0f}м  {current_speed:10.1f}м/с  {thrust_kn:8.1f}кН"
            )

        # Отделение ступеней
        if vessel.thrust == 0 and vessel.control.current_stage > 1:
            print(f"\nОтделение ступени на {current_time:.1f}с")
            vessel.control.activate_next_stage()
            time.sleep(1)

        time.sleep(0.1)

except Exception as e:
    print(f"\nОшибка: {e}")

print(f"\n3. ПОЛЕТ ЗАВЕРШЕН")
print(f"   Собрано точек: {len(times)}")
print(f"   Общее время: {times[-1]:.1f} с")
vessel.auto_pilot.disengage()

# Конвертируем в numpy
times = np.array(times)
speeds = np.array(speeds)
altitudes = np.array(altitudes)
thrusts = np.array(thrusts)

# ============================================================================
# ОБРАБОТКА ДАННЫХ
# ============================================================================

print("\n4. ОБРАБОТКА ДАННЫХ...")

# Сглаживаем скорость для графика
if len(speeds) > 5:
    window_size = min(9, len(speeds) // 10)
    if window_size % 2 == 0:
        window_size += 1
    speeds_smooth = np.convolve(speeds, np.ones(window_size) / window_size, mode="same")

    # Корректируем края
    edge = window_size // 2
    speeds_smooth[:edge] = speeds[:edge]
    speeds_smooth[-edge:] = speeds[-edge:]

    print(f"Скорость сглажена (окно {window_size} точек)")
    speeds_final = speeds_smooth
else:
    speeds_final = speeds

# Определяем момент отделения ускорителей по падению тяги
t_sep = None
sep_speed = None
sep_idx = None

if len(thrusts) > 50:
    for i in range(20, len(thrusts) - 10):
        if thrusts[i] < thrusts[i - 1] * 0.4 and thrusts[i] > 0:
            # Проверяем, что после падения тяга снова растет (включение основного двигателя)
            if i + 10 < len(thrusts) and thrusts[i + 10] > thrusts[i] * 1.5:
                t_sep = times[i]
                sep_speed = speeds_final[i] if "speeds_final" in locals() else speeds[i]
                sep_idx = i
                print(
                    f"Обнаружено отделение ускорителей на {t_sep:.1f} с, скорость {sep_speed:.0f} м/с"
                )
                break

if t_sep is None:
    # Если не нашли автоматически, используем значение из предыдущих запусков
    t_sep = 76.6
    # Находим ближайшую точку
    if len(times) > 0:
        sep_idx = np.argmin(np.abs(times - t_sep))
        sep_speed = (
            speeds_final[sep_idx] if "speeds_final" in locals() else speeds[sep_idx]
        )
    print(f"Используем значение по умолчанию: отделение на {t_sep:.1f} с")

print(f"\nСТАТИСТИКА:")
print(f"- Время: {times[0]:.1f} - {times[-1]:.1f} с")
print(f"- Скорость: {speeds_final[0]:.1f} - {speeds_final[-1]:.1f} м/с")
print(f"- Максимальная скорость: {np.max(speeds_final):.1f} м/с")
print(f"- Высота в конце: {altitudes[-1]/1000:.1f} км")

# ============================================================================
# ГРАФИК: v(t) - СКОРОСТЬ ОТ ВРЕМЕНИ (как на фото)
# ============================================================================

print("\n5. ПОСТРОЕНИЕ ГРАФИКА...")

fig, ax = plt.subplots(figsize=(14, 8))

# 1. Основная линия - СКОРОСТЬ ИЗ KSP (синяя, как на фото)
ax.plot(
    times,
    speeds_final,
    "b-",
    linewidth=3.5,
    label="Скорость ракеты (KSP)",
    zorder=5,
    alpha=0.95,
)

# 2. Разметка графика
# Зона ускорителей (синяя заливка)
ax.axvspan(
    0,
    t_sep,
    alpha=0.08,
    color="blue",
    label="4 ускорителя (основной выключен)",
    zorder=1,
)

# Зона основного двигателя (зелёная заливка)
ax.axvspan(
    t_sep, 150, alpha=0.08, color="green", label="Только основной двигатель", zorder=1
)

# Линия отделения ускорителей
ax.axvline(x=t_sep, color="red", linestyle="--", linewidth=2.5, alpha=0.8, zorder=4)
ax.text(
    t_sep + 2,
    100,
    f"Отделение ускорителей\n{t_sep:.1f} с",
    fontsize=11,
    color="red",
    verticalalignment="bottom",
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
    zorder=6,
)

# 3. Настройка осей
ax.set_xlabel("Время полета, с", fontsize=14, fontweight="bold", labelpad=10)
ax.set_ylabel("Скорость ракеты, м/с", fontsize=14, fontweight="bold", labelpad=10)
ax.set_title(
    "График зависимости скорости ракеты от времени\n(Экспериментальные данные KSP)",
    fontsize=16,
    fontweight="bold",
    pad=20,
)

# Границы как на фото
ax.set_xlim(0, 150)
ax.set_ylim(0, 1800)

# Сетка
ax.set_xticks(np.arange(0, 151, 25))
ax.set_yticks(np.arange(0, 1801, 250))
minor_xticks = np.arange(0, 151, 5)
minor_yticks = np.arange(0, 1801, 100)
ax.set_xticks(minor_xticks, minor=True)
ax.set_yticks(minor_yticks, minor=True)
ax.grid(True, which="major", linestyle="-", alpha=0.3, linewidth=1.0)
ax.grid(True, which="minor", linestyle=":", alpha=0.2, linewidth=0.5)

# 4. Легенда
ax.legend(loc="lower right", fontsize=12, framealpha=0.95)

# 5. Ключевые точки (как на фото)
if len(times) > 0:
    # Точка отделения ускорителей
    if sep_idx is not None:
        sep_speed_val = speeds_final[sep_idx]
        ax.plot(
            t_sep,
            sep_speed_val,
            "ro",
            markersize=10,
            markeredgecolor="darkred",
            markerfacecolor="red",
            markeredgewidth=2,
            zorder=7,
        )
        ax.text(
            t_sep + 5,
            sep_speed_val + 50,
            f"{sep_speed_val:.0f} м/с",
            fontsize=11,
            color="darkred",
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
            zorder=8,
        )

    # Точка на 140 секундах
    idx_140 = np.argmin(np.abs(times - 140))
    if idx_140 < len(speeds_final):
        v_140 = speeds_final[idx_140]
        ax.plot(
            140,
            v_140,
            "bo",
            markersize=10,
            markeredgecolor="darkblue",
            markerfacecolor="blue",
            markeredgewidth=2,
            zorder=7,
        )
        ax.annotate(
            f"140 с: {v_140:.0f} м/с",
            xy=(140, v_140),
            xytext=(140 - 30, v_140 + 120),
            fontsize=12,
            color="darkblue",
            fontweight="bold",
            arrowprops=dict(
                arrowstyle="->", color="darkblue", alpha=0.8, linewidth=1.5
            ),
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="white",
                alpha=0.95,
                edgecolor="blue",
            ),
            zorder=8,
        )

    # Точка на 150 секундах
    idx_150 = np.argmin(np.abs(times - 150))
    if idx_150 < len(speeds_final):
        v_150 = speeds_final[idx_150]
        ax.plot(
            150,
            v_150,
            "go",
            markersize=12,
            markeredgecolor="darkgreen",
            markerfacecolor="green",
            markeredgewidth=2,
            zorder=7,
        )
        ax.annotate(
            f"150 с: {v_150:.0f} м/с",
            xy=(150, v_150),
            xytext=(150 - 35, v_150 + 150),
            fontsize=13,
            color="darkgreen",
            fontweight="bold",
            arrowprops=dict(
                arrowstyle="->", color="darkgreen", alpha=0.8, linewidth=1.5
            ),
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="white",
                alpha=0.95,
                edgecolor="green",
            ),
            zorder=8,
        )

    for t_point in [25, 50, 75, 100, 125]:
        if t_point <= times[-1]:
            idx = np.argmin(np.abs(times - t_point))
            if idx < len(speeds_final):
                speed_val = speeds_final[idx]
                ax.plot(t_point, speed_val, "g.", markersize=8, alpha=0.7, zorder=6)

# 6. Линия орбитальной скорости Кербина (~2300 м/с)
orbital_v = 2300
if orbital_v <= 1800:  # если в пределах графика
    ax.axhline(
        y=orbital_v, color="purple", linestyle="-.", linewidth=2.0, alpha=0.6, zorder=3
    )
    ax.text(
        10,
        orbital_v + 50,
        f"Орбитальная скорость\n~{orbital_v} м/с",
        fontsize=10,
        color="purple",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
    )

plt.tight_layout()

# Сохраняем график
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"ksp_speed_vs_time_эксперимент_{timestamp}.png"
plt.savefig(filename, dpi=300, bbox_inches="tight")
print(f"\n✅ ГРАФИК СОХРАНЕН: {filename}")

# ============================================================================
# ВЫВОД ДАННЫХ ДЛЯ СРАВНЕНИЯ
# ============================================================================

print("\n" + "=" * 60)
print("КЛЮЧЕВЫЕ ТОЧКИ ДЛЯ СРАВНЕНИЯ С ТЕОРЕТИЧЕСКИМ ГРАФИКОМ:")
print("=" * 60)

if len(times) > 0:
    for t in [25, 50, 75, 100, 125, 140, 150]:
        idx = np.argmin(np.abs(times - t))
        if idx < len(speeds_final):
            v_at_t = speeds_final[idx]
            h_at_t = altitudes[idx] / 1000
            print(f"t={t:3d} с: v={v_at_t:6.1f} м/с, h={h_at_t:5.1f} км")

print("\n" + "=" * 60)
print("=" * 60)

# Показываем график
plt.show()
