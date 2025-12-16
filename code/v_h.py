import numpy as np
import matplotlib.pyplot as plt
import math

# Константы Кербина
R = 600000.0  # м
g0 = 9.81  # м/с²
rho0 = 1.223  # кг/м³
H_atm = 5000.0  # м

# Параметры ракеты
M0 = 439000.0  # кг
F_b = 1515000.0  # Н (один ускоритель)
F_m = 1443000.0  # Н
Isp_b = 205.0  # с
Isp_m = 275.0  # с
Cd = 0.25
A = 7.07  # м²

# Расходы
mdot_b = F_b / (Isp_b * g0)  # одного ускорителя
mdot_4b = mdot_b * 4  # четырёх
mdot_m = F_m / (Isp_m * g0)  # основного
mdot_total = mdot_4b + mdot_m  # общий

# Суммарная тяга
F_total = 4 * F_b + F_m

print("=== ПАРАМЕТРЫ ===")
print(f"Стартовая масса: {M0/1000:.1f} т")
print(f"Суммарная тяга: {F_total/1e6:.2f} МН")
print(f"Суммарный расход: {mdot_total:.1f} кг/с")
print()

# Начальные условия
h = 0.0  # высота, м
vx = 0.0  # горизонтальная скорость, м/с
vy = 0.0  # вертикальная скорость, м/с
m = M0  # масса, кг
t = 0.0  # время, с
dt = 0.1  # шаг интегрирования, с

# Массивы для результатов
heights = []
velocities = []


# Функции
def rho_atm(h):
    return rho0 * math.exp(-h / H_atm)


def gravity(h):
    return g0 * (R / (R + h)) ** 2


def get_pitch(h, vx):
    """Определение угла тангажа по высоте и горизонтальной скорости"""
    if h < 800:
        return 90.0
    elif h < 25000:
        # Линейный разворот от 90° до 10°
        return 90 - (h - 800) / (25000 - 800) * 80
    else:
        if vx > 800:
            return 5.0
        else:
            return 10.0


# Основной цикл моделирования
print("Моделирование полёта...")
while h < 70000:  # моделируем до 70 км высоты
    # 1. Угол тангажа
    pitch = get_pitch(h, vx)
    theta = math.radians(pitch)

    # 2. Полная скорость
    v = math.sqrt(vx**2 + vy**2) if (vx != 0 or vy != 0) else 0

    # 3. Атмосфера и гравитация
    rho = rho_atm(h)
    g = gravity(h)

    # 4. Сила сопротивления
    D = 0.5 * rho * v**2 * Cd * A
    if v > 0:
        Dx = D * (vx / v)
        Dy = D * (vy / v)
    else:
        Dx, Dy = 0, 0

    # 5. Ускорения
    ax = (F_total * math.cos(theta) - Dx) / m
    ay = (F_total * math.sin(theta) - Dy) / m - g

    # 6. Интегрирование
    vx += ax * dt
    vy += ay * dt
    h += vy * dt
    m -= mdot_total * dt
    t += dt

    # 7. Сохранение результатов
    v_total = math.sqrt(vx**2 + vy**2)
    heights.append(h)
    velocities.append(v_total)

    # Защита от исчерпания топлива
    if m < M0 * 0.1:  # если осталось меньше 10% массы
        print(f"⚠️ Топливо на исходе на высоте {h/1000:.1f} км!")
        break

print(f"Моделирование завершено на высоте {h/1000:.1f} км")
print(f"Время моделирования: {t:.1f} с")
print(f"Конечная скорость: {velocities[-1]:.1f} м/с")
print()

# ============================================================================
#  Зависимость скорости от высоты
# ============================================================================

plt.figure(figsize=(12, 8))

# Конвертируем высоту в километры для графика
heights_km = np.array(heights) / 1000
velocities_arr = np.array(velocities)

# Построение графика
plt.plot(
    velocities_arr,
    heights_km,
    "b-",
    linewidth=3.0,
    label="Теоретическая модель (уравнение Мещерского)",
)

# Настройка осей
plt.xlabel("Скорость, м/с", fontsize=14, fontweight="bold")
plt.ylabel("Высота, км", fontsize=14, fontweight="bold")
plt.title("Зависимость скорости ракеты от высоты", fontsize=16, fontweight="bold")

# ГРАНИЦЫ
plt.xlim(0, 1200)
plt.ylim(0, 70)

# Сетка
plt.xticks(np.arange(0, 1201, 200))
plt.yticks(np.arange(0, 71, 10))
minor_xticks = np.arange(0, 1201, 100)
minor_yticks = np.arange(0, 71, 5)
plt.xticks(minor_xticks, minor=True)
plt.yticks(minor_yticks, minor=True)
plt.grid(True, which="major", linestyle="-", alpha=0.3, linewidth=1.0)
plt.grid(True, which="minor", linestyle=":", alpha=0.2, linewidth=0.5)

# Добавляем основные горизонтальные линии
for y in [10, 20, 30, 40, 50, 60]:
    plt.axhline(y=y, color="gray", linestyle=":", alpha=0.3, linewidth=0.8)

# Добавляем основные вертикальные линии
for x in [200, 400, 600, 800, 1000]:
    plt.axvline(x=x, color="gray", linestyle=":", alpha=0.3, linewidth=0.8)

# Легенда
plt.legend(loc="lower right", fontsize=12, framealpha=0.95)

# Ключевые точки высоты
key_heights = [10, 20, 30, 40, 50, 60]
for h_key in key_heights:
    # Находим ближайшую точку к этой высоте
    if len(heights_km) > 0:
        idx = np.argmin(np.abs(heights_km - h_key))
        if idx < len(velocities_arr):
            v_at_h = velocities_arr[idx]
            # Отмечаем точку, если она в пределах графика
            if 0 <= v_at_h <= 1200:
                plt.plot(v_at_h, heights_km[idx], "ro", markersize=6, alpha=0.7)
                plt.text(
                    v_at_h + 10,
                    heights_km[idx] + 1,
                    f"{h_key} км: {v_at_h:.0f} м/с",
                    fontsize=9,
                    color="red",
                    alpha=0.8,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8),
                )

plt.tight_layout()

# Сохраняем график для будущего сравнения
plt.savefig("график_скорость_от_высоты_теория.png", dpi=300, bbox_inches="tight")
print("✅ График сохранен как 'график_скорость_от_высоты_теория.png'")


plt.show()

# Дополнительная статистика
print("\n" + "=" * 60)
print("СТАТИСТИКА ДЛЯ КЛЮЧЕВЫХ ВЫСОТ")
print("=" * 60)

if len(heights_km) > 0 and len(velocities_arr) > 0:
    for h_key in [10, 20, 30, 40, 50, 60]:
        # Находим ближайшую точку к этой высоте
        idx = np.argmin(np.abs(heights_km - h_key))
        if idx < len(velocities_arr):
            v_at_h = velocities_arr[idx]
            t_at_h = idx * dt  # приблизительное время
            print(
                f"Высота {h_key:2d} км: скорость = {v_at_h:6.1f} м/с, время ≈ {t_at_h:5.1f} с"
            )
