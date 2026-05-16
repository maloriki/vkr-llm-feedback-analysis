"""
BPMN AS-IS — waterfall-компоновка.

Горизонтальные дорожки (swim lanes), но задачи последовательно переходят
из верхней дорожки в нижнюю: первая задача сверху, последняя — внизу.
Это корректный BPMN 2.0 с логическим "каскадом" процесса.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 11))
ax.set_xlim(0, 18)
ax.set_ylim(0, 11)
ax.axis('off')
fig.patch.set_facecolor('white')

# --- цвета по ролям ---
COLORS = {
    'dwh':  ('#F5F0E0', '#B8A060'),
    'op':   ('#DAE8FC', '#6C8EBF'),
    'dash': ('#D5E8D4', '#82B366'),
    'mgr':  ('#E1D5E7', '#9673A6'),
    'lead': ('#FFE6CC', '#D79B00'),
}
ARROW = '#333333'
TIMER = '#E6882A'
END_COLOR = '#CC0000'
GATEWAY_FILL = '#FFF2CC'
GATEWAY_BORDER = '#D6B656'
LANE_BORDER = '#999999'
EN = '\u2013'


# --- swim lanes: сверху вниз (первое действие наверху) ---
POOL_X = 0.3
POOL_W = 1.4
LANES_X = POOL_X + POOL_W
LANES_W = 17.3

# порядок сверху вниз:
# 1. DWH (начало)
# 2. Оп. аналитик
# 3. Дашборд
# 4. Менеджер
# 5. Руководитель (конец)
LANES = [
    # (название, цвет_фона, y_center, h)
    ('dwh',  'Аналитик данных\n(DWH)',    '#FCFAF5', 9.2, 1.4),
    ('op',   'Операционный\nаналитик',     '#F7F9FD', 7.6, 1.4),
    ('dash', 'Дашборд\n(автомат.)',        '#F5FCF5', 6.0, 1.4),
    ('mgr',  'Менеджер',                   '#FAF5FE', 4.4, 1.4),
    ('lead', 'Руководитель',               '#FEFAF5', 2.8, 1.4),
]

BH = 0.75  # высота задачи


def draw_pool_and_lanes():
    # Пул (общий контейнер слева)
    lane_top = LANES[0][3] + LANES[0][4] / 2
    lane_bot = LANES[-1][3] - LANES[-1][4] / 2
    pool = FancyBboxPatch((POOL_X, lane_bot), POOL_W, lane_top - lane_bot,
                          boxstyle="square,pad=0",
                          facecolor='#E8E8E8', edgecolor=LANE_BORDER, linewidth=1.5)
    ax.add_patch(pool)
    ax.text(POOL_X + POOL_W / 2, (lane_top + lane_bot) / 2,
            'Процесс анализа\nобратной связи\n(AS-IS)',
            ha='center', va='center', fontsize=9, fontweight='bold',
            color='#333333', rotation=90)

    # Каждая дорожка
    for role, label, color, y, h in LANES:
        lane = FancyBboxPatch((LANES_X, y - h/2), LANES_W, h,
                              boxstyle="square,pad=0",
                              facecolor=color, edgecolor=LANE_BORDER, linewidth=0.8)
        ax.add_patch(lane)
        # Подпись роли внутри дорожки слева
        ax.text(LANES_X + 0.7, y, label,
                ha='center', va='center', fontsize=9, fontweight='bold',
                color='#555555')


def task(x, y, w, lines, role, fs=9):
    fill, border = COLORS[role]
    box = FancyBboxPatch((x - w/2, y - BH/2), w, BH,
                         boxstyle="round,pad=0.06",
                         facecolor=fill, edgecolor=border, linewidth=1.4)
    ax.add_patch(box)
    n = len(lines)
    for i, line in enumerate(lines):
        off = (n - 1) / 2 - i
        ax.text(x, y + off * 0.24, line,
                ha='center', va='center', fontsize=fs, color='#333333')


def lane_y(role_key):
    for role, _, _, y, _ in LANES:
        if role == role_key:
            return y
    raise ValueError(role_key)


def start_event(x, y, r=0.22, timer=False):
    c = plt.Circle((x, y), r, fill=False,
                   edgecolor=TIMER if timer else '#67AB49', linewidth=2.5)
    ax.add_patch(c)
    if timer:
        ax.plot([x, x], [y, y + r*0.6], color=TIMER, linewidth=1.5)
        ax.plot([x, x + r*0.4], [y, y], color=TIMER, linewidth=1.5)


def end_event(x, y, r=0.22):
    c = plt.Circle((x, y), r, fill=True, facecolor=END_COLOR,
                   edgecolor=END_COLOR, linewidth=2.5)
    ax.add_patch(c)


def gateway(x, y, s=0.3):
    d = plt.Polygon([(x, y+s), (x+s, y), (x, y-s), (x-s, y)],
                    fill=True, facecolor=GATEWAY_FILL,
                    edgecolor=GATEWAY_BORDER, linewidth=1.5)
    ax.add_patch(d)
    ax.text(x, y, 'X', ha='center', va='center', fontsize=10,
            fontweight='bold', color=GATEWAY_BORDER)


def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=ARROW, lw=1.3))


def arrow_lane_down(x_from, x_to, y_from_lane, y_to_lane):
    """Стрелка между дорожками: выходит вниз из задачи, идёт
    вниз до нужной дорожки, поворачивает и входит в следующую задачу."""
    # Вниз из задачи
    ax.plot([x_from, x_from], [y_from_lane - BH/2, y_to_lane], color=ARROW, linewidth=1.3)
    if x_from != x_to:
        # Горизонтальный сегмент на уровне целевой дорожки
        ax.plot([x_from, x_to], [y_to_lane, y_to_lane], color=ARROW, linewidth=1.3)
    # Стрелка к таске
    arrow(x_to, y_to_lane, x_to, y_to_lane + 0.001)  # dummy to show arrowhead
    # лучше сделаем явно:


def connect_down(x1, y1_lane, x2, y2_lane):
    """Соединяет выход задачи (снизу) с входом следующей задачи (сверху)
    в нижележащей дорожке. Рисует L-образную или прямую линию + стрелку."""
    # Точка выхода — снизу первой задачи
    out_y = y1_lane - BH/2
    # Точка входа — сверху второй задачи
    in_y = y2_lane + BH/2

    if abs(x1 - x2) < 0.01:
        # Прямая линия вниз
        arrow(x1, out_y, x2, in_y)
    else:
        # L-форма: вниз, потом вбок, потом вверх (но чаще просто вниз и вбок)
        # Выбираем промежуточную точку — середину между дорожками
        mid_y = (out_y + in_y) / 2
        ax.plot([x1, x1], [out_y, mid_y], color=ARROW, linewidth=1.3)
        ax.plot([x1, x2], [mid_y, mid_y], color=ARROW, linewidth=1.3)
        arrow(x2, mid_y, x2, in_y)


# ===== TITLE =====
ax.text(9, 10.5, 'Модель бизнес-процесса AS-IS',
        ha='center', fontsize=14, fontweight='bold', color='#333333')
ax.text(9, 10.15, 'Нотация BPMN 2.0 | Процесс: сверху вниз (waterfall)',
        ha='center', fontsize=10, fontstyle='italic', color='#666666')

draw_pool_and_lanes()

# ===== FLOW =====
# Все задачи имеют увеличивающееся X, потом переход в нижнюю дорожку
# Это даёт waterfall-эффект

# DWH lane (y=9.2)
y1 = lane_y('dwh')
# Start event
sx = 3.2
start_event(sx, y1, timer=True)
ax.text(sx, y1 + 0.55, 'Еженедельно', ha='center', va='center',
        fontsize=8, color=TIMER, fontstyle='italic')

# T1: Выгрузка из OMS
t1x = 5.0
task(t1x, y1, 2.4, ['Выгрузка данных', 'из OMS'], 'dwh')
arrow(sx + 0.22, y1, t1x - 1.2, y1)

# Op. analyst lane (y=7.6)
y2 = lane_y('op')
# T2: Написание скрипта
t2x = 5.0
task(t2x, y2, 2.4, ['Написание скрипта', 'обработки данных'], 'op')
connect_down(t1x, y1, t2x, y2)

# T3: Выгрузка на дашборд
t3x = 8.0
task(t3x, y2, 2.4, ['Выгрузка данных', 'на дашборд'], 'op')
arrow(t2x + 1.2, y2, t3x - 1.2, y2)

# Dashboard lane (y=6.0)
y3 = lane_y('dash')
# T4: Автомат. отображение
t4x = 8.0
task(t4x, y3, 2.4, ['Автоматическое', 'отображение данных'], 'dash')
connect_down(t3x, y2, t4x, y3)

# Manager lane (y=4.4)
y4 = lane_y('mgr')
# T5: Просмотр дашборда
t5x = 8.0
task(t5x, y4, 2.6, ['Просмотр дашборда,', 'поиск по кл. словам'], 'mgr')
connect_down(t4x, y3, t5x, y4)

# T6: Выводы
t6x = 11.0
task(t6x, y4, 2.3, ['Формирование', 'выводов вручную'], 'mgr')
arrow(t5x + 1.3, y4, t6x - 1.15, y4)

# T7: Передача руководителю
t7x = 13.7
task(t7x, y4, 2.3, ['Передача выводов', 'руководителю'], 'mgr')
arrow(t6x + 1.15, y4, t7x - 1.15, y4)

# Leader lane (y=2.8)
y5 = lane_y('lead')
# T8: Анализ и решения
t8x = 13.7
task(t8x, y5, 2.3, ['Анализ и принятие', 'решений'], 'lead')
connect_down(t7x, y4, t8x, y5)

# Gateway
gw_x = 16.0
gateway(gw_x, y5)
arrow(t8x + 1.15, y5, gw_x - 0.3, y5)

# End event
end_x = 17.2
end_event(end_x, y5)
arrow(gw_x + 0.3, y5, end_x - 0.22, y5)
ax.text((gw_x + end_x) / 2, y5 + 0.25, 'Нет', ha='center', fontsize=7.5,
        color='#555555')

# Yes branch: вверх и обратно в "Формирование выводов"
ax.plot([gw_x, gw_x], [y5 + 0.3, y4 + BH/2 + 0.4], color=ARROW, linewidth=1.3)
ax.plot([gw_x, t6x], [y4 + BH/2 + 0.4, y4 + BH/2 + 0.4], color=ARROW, linewidth=1.3)
arrow(t6x, y4 + BH/2 + 0.4, t6x, y4 + BH/2)
ax.text(gw_x - 0.1, y5 + 0.5, 'Да', fontsize=7.5, color='#555555')
ax.text((gw_x + t6x) / 2, y4 + BH/2 + 0.55, 'Назначение задач',
        ha='center', fontsize=7.5, fontstyle='italic', color='#777777')

# ===== АННОТАЦИИ ПРОБЛЕМ =====
# Telegram не анализируется
ax.text(5.0, y1 - 0.7,
        'Telegram-чаты\nНЕ анализируются',
        ha='center', va='center', fontsize=7.5, color='#CC0000',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF0F0',
                  edgecolor='#CC6666', linewidth=0.8, linestyle='dashed', alpha=0.8))

# Ограничения дашборда
ax.text(11.5, y3,
        'Графики оценок,\nбез анализа текста',
        ha='center', va='center', fontsize=7.5, color='#CC0000',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF0F0',
                  edgecolor='#CC6666', linewidth=0.8, linestyle='dashed', alpha=0.8))

# Поиск по ключевым словам
ax.text(8.0, y4 + 0.9,
        'Ключевые слова не\nулавливают контекст',
        ha='center', va='center', fontsize=7.5, color='#CC0000',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF0F0',
                  edgecolor='#CC6666', linewidth=0.8, linestyle='dashed', alpha=0.8))

# Задержка
ax.text(14.8, y5 + 0.9, f'Задержка 1{EN}2 дня',
        ha='center', va='center', fontsize=7.5, color='#E6882A',
        fontstyle='italic', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF8EE',
                  edgecolor='#E6882A', linewidth=0.8, alpha=0.85))

# ===== BOTTOM BAR =====
ax.text(9, 1.6,
        'Узкое место: ручной поиск по ключевым словам без семантического анализа текста',
        ha='center', fontsize=10, fontweight='bold', color='#CC0000',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF0F0',
                  edgecolor='#CC0000', alpha=0.85, linewidth=1.2))

# ===== LEGEND =====
ly = 0.6
ax.text(0.4, ly, 'Легенда:', fontsize=9, fontweight='bold', color='#333333')

items = [
    (2.0, COLORS['dwh'], 'DWH'),
    (4.0, COLORS['op'], 'Оп. аналитик'),
    (6.5, COLORS['dash'], 'Дашборд'),
    (8.8, COLORS['mgr'], 'Менеджер'),
    (11.3, COLORS['lead'], 'Руководитель'),
]
for bx, (fill, border), label in items:
    box = FancyBboxPatch((bx, ly - 0.15), 0.4, 0.3,
                         boxstyle="round,pad=0.02",
                         facecolor=fill, edgecolor=border, linewidth=1.2)
    ax.add_patch(box)
    ax.text(bx + 0.55, ly, label, fontsize=8.5, va='center', color='#333333')

start_event(13.8, ly, r=0.12, timer=True)
ax.text(14.05, ly, 'Таймер', fontsize=8.5, va='center', color='#333333')

end_event(15.2, ly, r=0.12)
ax.text(15.45, ly, 'Конец', fontsize=8.5, va='center', color='#333333')

gateway(16.4, ly, s=0.15)
ax.text(16.65, ly, 'Условие', fontsize=8.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig2_BPMN_ASIS.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
