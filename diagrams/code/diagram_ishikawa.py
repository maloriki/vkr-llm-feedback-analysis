import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

fig, ax = plt.subplots(1, 1, figsize=(18, 10))
ax.set_xlim(0, 18)
ax.set_ylim(0, 10)
ax.axis('off')
fig.patch.set_facecolor('white')

# Цвета категорий
CATS = {
    'people':  ('#E8D5E8', '#9673A6'),
    'process': ('#DAE8FC', '#6C8EBF'),
    'tech':    ('#D5E8D4', '#82B366'),
    'data':    ('#FFF2CC', '#D6B656'),
    'time':    ('#FFE6CC', '#D79B00'),
}
SPINE = '#CC0000'
EFFECT_FILL = '#F8CECC'
EFFECT_BORDER = '#B85450'

# ===== TITLE =====
ax.text(9, 9.5,
        'Диаграмма Исикавы: корневые причины неэффективного анализа обратной связи',
        ha='center', fontsize=13, fontweight='bold', color='#333333')

# ===== MAIN SPINE =====
SPINE_Y = 5.0
SPINE_START = 1.0
SPINE_END = 14.8
ax.annotate('', xy=(SPINE_END, SPINE_Y), xytext=(SPINE_START, SPINE_Y),
            arrowprops=dict(arrowstyle='->', color=SPINE, lw=3.5))

# ===== EFFECT (right) =====
eff = FancyBboxPatch((14.8, SPINE_Y - 0.75), 2.8, 1.5,
                     boxstyle="round,pad=0.1",
                     facecolor=EFFECT_FILL, edgecolor=EFFECT_BORDER, linewidth=2)
ax.add_patch(eff)
ax.text(16.2, SPINE_Y + 0.2, 'Неэффективный',
        ha='center', fontsize=11, fontweight='bold', color=EFFECT_BORDER)
ax.text(16.2, SPINE_Y - 0.15, 'анализ обратной',
        ha='center', fontsize=11, fontweight='bold', color=EFFECT_BORDER)
ax.text(16.2, SPINE_Y - 0.5, 'связи',
        ha='center', fontsize=11, fontweight='bold', color=EFFECT_BORDER)


def draw_category(spine_x, side, name, color_key, causes):
    """
    Рисует категорию: блок-заголовок + наклонная ветка к хребту + причины на ветке.

    side: 'top' или 'bottom'
    causes: список строк (до 3-х причин)
    """
    fill, border = CATS[color_key]

    # Длина диагональной ветки
    branch_len = 3.0
    # Угол — для эстетики
    if side == 'top':
        y_end = SPINE_Y + branch_len
    else:
        y_end = SPINE_Y - branch_len

    # Категорийный блок на конце ветки
    block_w = 2.5
    block_h = 0.55
    ax.add_patch(FancyBboxPatch(
        (spine_x - block_w/2, y_end - block_h/2),
        block_w, block_h, boxstyle="round,pad=0.05",
        facecolor=fill, edgecolor=border, linewidth=2
    ))
    ax.text(spine_x, y_end, name,
            ha='center', va='center', fontsize=10, fontweight='bold', color='#333333')

    # Диагональная ветка от хребта до блока
    # Заканчиваем чуть раньше блока
    tip_offset = block_h / 2 + 0.05
    y_branch_end = y_end - tip_offset if side == 'top' else y_end + tip_offset
    ax.plot([spine_x, spine_x], [SPINE_Y, y_branch_end],
            color=border, linewidth=2.5)

    # Причины — 3 штуки на ветке, каждая на своей высоте
    n = len(causes)
    for i, cause in enumerate(causes):
        # Равномерно распределяем по длине ветки
        t = (i + 1) / (n + 1)
        if side == 'top':
            cy = SPINE_Y + branch_len * t
            text_offset = 0.05
        else:
            cy = SPINE_Y - branch_len * t
            text_offset = -0.05

        # Линия-стрелка от хребта к причине
        # Уменьшим длину линии в зависимости от уровня
        line_len = 1.1
        # Левая/правая сторона — чередуем
        dir_x = -1 if i % 2 == 0 else 1
        x_start = spine_x
        x_end = spine_x + dir_x * line_len

        ax.annotate('', xy=(spine_x, cy),
                    xytext=(x_end, cy),
                    arrowprops=dict(arrowstyle='-', color=border,
                                    lw=1.2, linestyle='-'))

        ax.text(x_end + dir_x * 0.08, cy + text_offset, cause,
                ha='right' if dir_x < 0 else 'left',
                va='center', fontsize=8, color='#444444')


# ===== ВЕРХНИЕ КАТЕГОРИИ =====
draw_category(3.5, 'top', 'Персонал', 'people', [
    'Субъективность оценок',
    'Потеря контекста\nпри текучести',
    'Невоспроизводимость\nвыводов',
])

draw_category(7.0, 'top', 'Процесс', 'process', [
    'Нет методологии',
    'Telegram-чаты не\nанализируются',
    'Линейная передача\nинформации',
])

draw_category(11.0, 'top', 'Технологии', 'tech', [
    'Нет NLP/LLM\nинструментов',
    'Excel как\nединственное средство',
    'Поиск по\nключевым словам',
])


# ===== НИЖНИЕ КАТЕГОРИИ =====
draw_category(4.5, 'bottom', 'Данные', 'data', [
    'Объём превышает\nвозможности',
    'Мультиисточниковость\n(отзывы + чаты)',
    'Неструктурирован-\nный текст',
])

draw_category(9.5, 'bottom', 'Время', 'time', [
    'Задержка 1–2 дня',
    'Реактивная\nаналитика',
    'Устаревание\nотчётов',
])


# ===== LEGEND =====
ly = 0.3
ax.text(1.0, ly, 'Легенда:', fontsize=9, fontweight='bold', color='#333333')

items = [
    ('Персонал', CATS['people']),
    ('Процесс', CATS['process']),
    ('Технологии', CATS['tech']),
    ('Данные', CATS['data']),
    ('Время', CATS['time']),
]
for i, (label, (fill, border)) in enumerate(items):
    lx = 2.5 + i * 2.6
    box = FancyBboxPatch((lx, ly - 0.15), 0.4, 0.3,
                        boxstyle="round,pad=0.02",
                        facecolor=fill, edgecolor=border, linewidth=1.2)
    ax.add_patch(box)
    ax.text(lx + 0.55, ly, label, fontsize=8.5, va='center', color='#333333')

ebox = FancyBboxPatch((15.6, ly - 0.15), 0.4, 0.3,
                     boxstyle="round,pad=0.02",
                     facecolor=EFFECT_FILL, edgecolor=EFFECT_BORDER, linewidth=1.2)
ax.add_patch(ebox)
ax.text(16.1, ly, 'Следствие', fontsize=8.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig3_Ishikawa.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
