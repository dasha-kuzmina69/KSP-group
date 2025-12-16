import numpy as np
import matplotlib.pyplot as plt
import math

# Константы Кербина
R = 600000.0  # м
g0 = 9.81  # м/с²
rho0 = 1.223  # кг/м³
H_atm = 5000.0  # м

# Параметры ракеты (оригинальные)
M0 = 439000.0  # кг
F_b = 1515000.0  # Н (один ускоритель)
F_m = 1443000.0  # Н (основной двигатель)
Isp_b = 205.0  # с (ускорители)
Isp_m = 275.0  # с (основной)
Cd = 0.25
A = 7.07  # м²

# Расходы
mdot_b = F_b / (Isp_b * g0)  # одного ускорителя
mdot_4b = mdot_b * 4  # четырёх ускорителей
mdot_m = F_m / (Isp_m * g0)  # основного двигателя

# Масса ускорителей с топливом
m_boosters_with_fuel = 240000.0  # кг
# Масса после сброса ускорителей (примерно)
m_after_boosters = M0 - m_boosters_with_fuel

# Время работы ускорителей
t_boost = m_boosters_with_fuel / mdot_4b  # ~79.5 с

# Топливо основной ступени
m_fuel_stage1 = 118000.0  # кг
t_main_max = m_fuel_stage1 / mdot_m  # время работы основного двигателя

print("=== ПАРАМЕТРЫ ===")
print(f"Стартовая масса: {M0/1000:.1f} т")
print(f"Тяга 4 ускорителей: {4*F_b/1e6:.2f} МН")
print(f"Тяга основного двигателя: {F_m/1e6:.2f} МН")
print(f"Время работы ускорителей: {t_boost:.1f} с")
print()


# Функции
def rho_atm(h):
    return rho0 * math.exp(-h / H_atm)


def gravity(h):
    return g0 * (R / (R + h)) ** 2


def get_pitch(h, vx):
    """Угол тангажа по высоте и горизонтальной скорости"""
    if h < 800:
        return 90.0
    elif h < 25000:
        return 90 - (h - 800) / (25000 - 800) * 80
    else:
        if vx > 800:
            return 5.0
        else:
            return 10.0


# (уравнение Мещерского) - ДО 150 СЕКУНД
print("Численное моделирование (до 150 секунд)...")
h = 0.0
vx = 0.0
vy = 0.0
m = M0
t = 0.0
dt = 0.1

times_num = []
velocities_num = []
heights_num = []
masses_num = []

# Моделируем до 150 секунд
while t <= 150.0:
    # Определяем, какие двигатели работают
    if t < t_boost:
        # Фаза 1: ТОЛЬКО 4 ускорителя, основной двигатель ВЫКЛЮЧЕН
        F = 4 * F_b
        mdot = mdot_4b
    else:
        # Фаза 2: ТОЛЬКО основной двигатель (ускорители сброшены)
        F = F_m
        mdot = mdot_m
        # В момент сброса мгновенно уменьшаем массу
        if t - dt < t_boost <= t:
            m = m_after_boosters  # сбрасываем ускорители

    # Угол тангажа
    pitch = get_pitch(h, vx)
    theta = math.radians(pitch)

    # Полная скорость
    v = math.sqrt(vx**2 + vy**2) if (vx != 0 or vy != 0) else 0

    # Атмосфера и гравитация
    rho = rho_atm(h)
    g = gravity(h)

    # Сила сопротивления
    D = 0.5 * rho * v**2 * Cd * A
    if v > 0:
        Dx = D * (vx / v)
        Dy = D * (vy / v)
    else:
        Dx, Dy = 0, 0

    # Ускорения (уравнение Мещерского)
    ax = (F * math.cos(theta) - Dx) / m
    ay = (F * math.sin(theta) - Dy) / m - g

    # Интегрирование
    vx += ax * dt
    vy += ay * dt
    h += vy * dt
    m -= mdot * dt
    t += dt

    # Сохранение
    v_total = math.sqrt(vx**2 + vy**2)
    times_num.append(t)
    velocities_num.append(v_total)
    heights_num.append(h)
    masses_num.append(m)

# (формула Циолковского) - ДО 150 СЕКУНД
print("Аналитический расчёт (до 150 секунд)...")


def calculate_ideal_velocity():
    """Рассчитывает идеальную скорость по формуле Циолковского"""
    times_ideal = np.linspace(0, min(150.0, t_boost + t_main_max), 1000)
    velocities_ideal = []

    for t_val in times_ideal:
        if t_val < t_boost:
            # Фаза 1: только ускорители
            m_t = M0 - mdot_4b * t_val
            if m_t > m_after_boosters:
                v_ideal = Isp_b * g0 * math.log(M0 / m_t)
            else:
                # Доходим до момента сброса
                m_at_sep = m_after_boosters
                v_to_sep = Isp_b * g0 * math.log(M0 / m_at_sep)
                v_ideal = v_to_sep
        else:
            # Фаза 2: только основной двигатель
            # Масса в момент сброса
            m_at_sep = m_after_boosters
            # Скорость в момент сброса
            v_at_sep = Isp_b * g0 * math.log(M0 / m_at_sep)
            # Время работы основного двигателя
            t_main = t_val - t_boost
            m_t_main = m_at_sep - mdot_m * t_main
            if m_t_main > m_at_sep * 0.3:
                v_ideal = v_at_sep + Isp_m * g0 * math.log(m_at_sep / m_t_main)
            else:
                v_ideal = v_at_sep

        velocities_ideal.append(v_ideal)

    return times_ideal, velocities_ideal


times_ideal, velocities_ideal = calculate_ideal_velocity()

# ============================================================================
# скорость от времени (0-150 секунд, 0-2000 м/с)
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

# 1. Основная линия - РЕАЛЬНАЯ СКОРОСТЬ
ax.plot(
    times_num,
    velocities_num,
    "b-",
    linewidth=3.5,
    label="Скорость ракеты (уравнение Мещерского)",
    zorder=5,
    alpha=0.95,
)

# 2. Идеальная скорость - красный пунктир (ЯРКИЙ И ТОЛСТЫЙ)
ax.plot(
    times_ideal,
    velocities_ideal,
    "r--",
    linewidth=3.0,
    label="Идеальная скорость (формула Циолковского)",
    alpha=0.9,
    zorder=6,
    dashes=(6, 3),
)

# 3. Разметка графика
t_sep = t_boost

# Зона ускорителей
ax.axvspan(
    0,
    t_sep,
    alpha=0.07,
    color="blue",
    label="4 ускорителя (основной выключен)",
    zorder=1,
)

# Зона основного двигателя
ax.axvspan(
    t_sep, 150, alpha=0.07, color="green", label="Только основной двигатель", zorder=1
)

# Линия отделения ускорителей
ax.axvline(x=t_sep, color="darkred", linestyle=":", linewidth=2.0, alpha=0.7, zorder=4)

# Текст отделения ускорителей (сбоку, не на графике)
ax.text(
    t_sep,
    -150,
    f"Отделение ускорителей\n{t_sep:.1f} с",
    fontsize=11,
    color="darkred",
    fontweight="bold",
    ha="center",
    va="top",
    bbox=dict(
        boxstyle="round,pad=0.4", facecolor="white", alpha=0.95, edgecolor="darkred"
    ),
    zorder=10,
)

# 4. Настройка осей
ax.set_xlabel("Время полета, с", fontsize=14, fontweight="bold", labelpad=10)
ax.set_ylabel("Скорость ракеты, м/с", fontsize=14, fontweight="bold", labelpad=10)
ax.set_title(
    "График зависимости скорости ракеты от времени",
    fontsize=16,
    fontweight="bold",
    pad=20,
)

# ГРАНИЦЫ
ax.set_xlim(0, 150)
ax.set_ylim(0, 2000)

# Сетка
ax.set_xticks(np.arange(0, 151, 25))
ax.set_yticks(np.arange(0, 2001, 250))
minor_xticks = np.arange(0, 151, 5)
minor_yticks = np.arange(0, 2001, 50)
ax.set_xticks(minor_xticks, minor=True)
ax.set_yticks(minor_yticks, minor=True)
ax.grid(True, which="major", linestyle="-", alpha=0.3, linewidth=1.0)
ax.grid(True, which="minor", linestyle=":", alpha=0.15, linewidth=0.5)

# 5. Легенда
ax.legend(loc="lower right", fontsize=12, framealpha=0.95)

# 6. Ключевые точки
if len(times_num) > 0:
    # Скорость в момент отделения
    idx_sep = min(range(len(times_num)), key=lambda i: abs(times_num[i] - t_sep))
    if idx_sep < len(velocities_num):
        v_sep = velocities_num[idx_sep]
        ax.plot(
            times_num[idx_sep],
            v_sep,
            "o",
            markersize=10,
            markeredgecolor="darkred",
            markerfacecolor="red",
            markeredgewidth=2,
            zorder=7,
        )

        # Подпись точки отделения
        ax.text(
            times_num[idx_sep] + 2,
            v_sep + 80,
            f"{v_sep:.0f} м/с",
            fontsize=11,
            color="darkred",
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="white", alpha=0.9, edgecolor="red"
            ),
            zorder=8,
        )

    # Скорость на 140 секундах (оригинальная граница)
    idx_140 = min(range(len(times_num)), key=lambda i: abs(times_num[i] - 140))
    if idx_140 < len(velocities_num):
        v_140 = velocities_num[idx_140]
        ax.plot(
            times_num[idx_140],
            v_140,
            "s",
            markersize=9,
            markeredgecolor="darkblue",
            markerfacecolor="blue",
            markeredgewidth=2,
            zorder=7,
        )

        # Подпись точки 140с
        ax.text(
            times_num[idx_140] + 2,
            v_140 - 100,
            f"140 с: {v_140:.0f} м/с",
            fontsize=11,
            color="darkblue",
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.3", facecolor="white", alpha=0.9, edgecolor="blue"
            ),
            zorder=8,
        )

    # Скорость на 150 секундах
    idx_150 = min(range(len(times_num)), key=lambda i: abs(times_num[i] - 150))
    if idx_150 < len(velocities_num):
        v_150 = velocities_num[idx_150]
        ax.plot(
            times_num[idx_150],
            v_150,
            "o",
            markersize=12,
            markeredgecolor="darkgreen",
            markerfacecolor="green",
            markeredgewidth=2,
            zorder=7,
        )

        # Подпись конечной точки
        ax.annotate(
            f"150 с: {v_150:.0f} м/с",
            xy=(times_num[idx_150], v_150),
            xytext=(times_num[idx_150] - 30, v_150 + 120),
            fontsize=12,
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

# 7. Вертикальная линия на 140 секундах (оригинальная граница)
ax.axvline(x=140, color="gray", linestyle="--", linewidth=1.5, alpha=0.5, zorder=3)
ax.text(
    140,
    1900,
    "140 с",
    fontsize=10,
    color="gray",
    ha="center",
    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8),
)

# 8. Горизонтальная линия орбитальной скорости Кербина (~2300 м/с)
orbital_v = 2300
ax.axhline(
    y=orbital_v, color="purple", linestyle="-.", linewidth=2.0, alpha=0.6, zorder=3
)
ax.text(
    10,
    orbital_v + 50,
    f"Орбитальная скорость Кербина\n~{orbital_v} м/с",
    fontsize=10,
    color="purple",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
)

plt.tight_layout()

# ВЫВОД РЕЗУЛЬТАТОВ
print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ (до 150 секунд)")
print("=" * 60)
if times_num:
    # В момент отделения
    idx_sep = min(range(len(times_num)), key=lambda i: abs(times_num[i] - t_sep))
    if idx_sep < len(velocities_num):
        print(
            f"Скорость при отделении ускорителей ({t_sep:.1f} с): {velocities_num[idx_sep]:.1f} м/с"
        )

    # На 140 секундах
    idx_140 = min(range(len(times_num)), key=lambda i: abs(times_num[i] - 140))
    if idx_140 < len(velocities_num):
        print(f"Скорость на 140 секундах: {velocities_num[idx_140]:.1f} м/с")

    # На 150 секундах
    idx_150 = min(range(len(times_num)), key=lambda i: abs(times_num[i] - 150))
    if idx_150 < len(velocities_num):
        print(f"Скорость на 150 секундах: {velocities_num[idx_150]:.1f} м/с")
        print(f"Высота на 150 секундах: {heights_num[idx_150]/1000:.1f} км")
        print(f"Масса на 150 секундах: {masses_num[idx_150]/1000:.1f} т")

    # Разница между реальной и идеальной скоростью
    if len(velocities_ideal) > 0:
        idx_ideal_150 = min(
            range(len(times_ideal)), key=lambda i: abs(times_ideal[i] - 150)
        )
        if idx_ideal_150 < len(velocities_ideal):
            v_ideal_150 = velocities_ideal[idx_ideal_150]
            v_real_150 = velocities_num[idx_150]
            loss = v_ideal_150 - v_real_150
            loss_percent = (loss / v_ideal_150) * 100
            print(f"\nИдеальная скорость на 150 с: {v_ideal_150:.1f} м/с")
            print(f"Суммарные потери скорости: {loss:.1f} м/с ({loss_percent:.1f}%)")
            print(f"Эффективность: {(1 - loss/v_ideal_150)*100:.1f}%")

print("\n" + "=" * 60)

# Сохраняем график
plt.savefig("график_скорость_время_150с.png", dpi=300, bbox_inches="tight")
print("✅ График сохранен как 'график_скорость_время_150с.png'")

plt.show()
