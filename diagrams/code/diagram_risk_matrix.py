import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import matplotlib.patches as mpatches
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(15, 10))
ax.set_xlim(0, 15)
ax.set_ylim(0, 10)
ax.axis('off')
fig.patch.set_facecolor('white')

# Colors for risk levels
LOW = '#82B366'       # green
MED = '#E6B85A'       # yellow
HIGH = '#D79B00'      # orange
CRIT = '#B85450'      # red

# ===== TITLE =====
ax.text(7.5, 9.6, 'Матрица рисков проекта внедрения ИАС',
        ha='center', fontsize=14, fontweight='bold', color='#333333')
ax.text(7.5, 9.2, 'Оценка по двум параметрам: вероятность возникновения и влияние на проект',
        ha='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== MATRIX (9 cells, 3x3) =====
# Cell positions: X (probability): low/med/high at x=3,6,9
# Y (impact): low/med/high at y=2,4.5,7
# Each cell is 3x2.5

# Risk level per cell (probability × impact)
#              Low_impact  Med_impact  High_impact
# Low_prob:    LOW         LOW         MED
# Med_prob:    LOW         MED         HIGH
# High_prob:   MED         HIGH        CRIT

matrix = {
    (0, 0): LOW,   (0, 1): LOW,   (0, 2): MED,
    (1, 0): LOW,   (1, 1): MED,   (1, 2): HIGH,
    (2, 0): MED,   (2, 1): HIGH,  (2, 2): CRIT,
}

matrix_labels = {
    (0, 0): 'Низкий',  (0, 1): 'Низкий',  (0, 2): 'Средний',
    (1, 0): 'Низкий',  (1, 1): 'Средний', (1, 2): 'Высокий',
    (2, 0): 'Средний', (2, 1): 'Высокий', (2, 2): 'Критический',
}

MX, MY = 3, 2  # matrix origin
CW, CH = 2.8, 2  # cell width, height

for (col, row), color in matrix.items():
    x = MX + col * CW
    y = MY + row * CH
    rect = Rectangle((x, y), CW, CH, facecolor=color, edgecolor='#333333',
                     linewidth=1, alpha=0.35)
    ax.add_patch(rect)
    # Level label
    ax.text(x + CW - 0.1, y + 0.15, matrix_labels[(col, row)],
            ha='right', va='bottom', fontsize=8, fontstyle='italic',
            color='#555555', fontweight='bold')

# ===== AXIS LABELS =====
# X axis (probability)
ax.text(MX + CW/2, MY - 0.4, 'Низкая', ha='center', fontsize=10, fontweight='bold')
ax.text(MX + CW * 1.5, MY - 0.4, 'Средняя', ha='center', fontsize=10, fontweight='bold')
ax.text(MX + CW * 2.5, MY - 0.4, 'Высокая', ha='center', fontsize=10, fontweight='bold')
ax.text(MX + CW * 1.5, MY - 0.9, 'ВЕРОЯТНОСТЬ',
        ha='center', fontsize=11, fontweight='bold', color='#333333')

# Y axis (impact)
ax.text(MX - 0.4, MY + CH/2, 'Низкое', ha='right', va='center', fontsize=10, fontweight='bold')
ax.text(MX - 0.4, MY + CH * 1.5, 'Среднее', ha='right', va='center', fontsize=10, fontweight='bold')
ax.text(MX - 0.4, MY + CH * 2.5, 'Высокое', ha='right', va='center', fontsize=10, fontweight='bold')
ax.text(MX - 1.3, MY + CH * 1.5, 'ВЛИЯНИЕ',
        ha='center', va='center', fontsize=11, fontweight='bold',
        color='#333333', rotation=90)


# ===== RISKS: (id, name, prob_idx, impact_idx, pos_in_cell) =====
# prob_idx: 0=low, 1=med, 2=high
# impact_idx: 0=low, 1=med, 2=high
# pos_in_cell: (dx, dy) offset within cell (0-1 range)

RISKS = [
    ('R1', 'Деградация качества LLM\nна специфич. данных', 1, 2, (0.3, 0.5)),
    ('R2', 'Недостаточная\nпроизв-ть GPU', 1, 1, (0.3, 0.5)),
    ('R3', 'Сбои облачных API', 2, 0, (0.3, 0.5)),
    ('R4', 'Ошибки парсинга\nJSON-ответов', 2, 1, (0.3, 0.5)),
    ('R5', 'Сопротивление\nперсонала', 1, 2, (0.7, 0.3)),
    ('R6', 'Отсутствие экспертизы\nпо промптам', 1, 1, (0.7, 0.3)),
    ('R7', 'Превышение\nбюджета', 0, 2, (0.5, 0.5)),
    ('R8', 'Изменение 152-ФЗ', 0, 2, (0.7, 0.2)),
    ('R9', 'Блокировка Telegram', 0, 1, (0.5, 0.5)),
    ('R10', 'Утечка ПДн\nчерез облако', 0, 2, (0.3, 0.8)),
    ('R11', 'Низкое качество\nисходных данных', 1, 1, (0.3, 0.2)),
    ('R12', 'Текучка кадров', 2, 0, (0.7, 0.5)),
]


for rid, name, p, i, (dx, dy) in RISKS:
    cx = MX + p * CW + dx * CW
    cy = MY + i * CH + dy * CH

    # Red circle marker
    circle = Circle((cx, cy), 0.25, facecolor='white', edgecolor='#CC0000',
                    linewidth=2, zorder=5)
    ax.add_patch(circle)
    ax.text(cx, cy, rid, ha='center', va='center', fontsize=8,
            fontweight='bold', color='#CC0000', zorder=6)


# ===== LEGEND (right side) =====
lx = 11.5
ly = 7.5

legend_title = ax.text(lx, ly + 0.4, 'Риски', fontsize=11, fontweight='bold',
                        color='#333333')

risk_labels = [
    ('R1', 'Деградация качества LLM'),
    ('R2', 'Недостаточная производительность GPU'),
    ('R3', 'Сбои облачных API'),
    ('R4', 'Ошибки парсинга JSON'),
    ('R5', 'Сопротивление персонала'),
    ('R6', 'Отсутствие экспертизы по промптам'),
    ('R7', 'Превышение бюджета'),
    ('R8', 'Изменение 152-ФЗ'),
    ('R9', 'Блокировка Telegram'),
    ('R10', 'Утечка ПДн через облако'),
    ('R11', 'Низкое качество данных'),
    ('R12', 'Текучка кадров'),
]

for idx, (rid, name) in enumerate(risk_labels):
    y = ly - idx * 0.38
    # Circle
    circle = Circle((lx, y), 0.12, facecolor='white', edgecolor='#CC0000',
                    linewidth=1.3)
    ax.add_patch(circle)
    ax.text(lx, y, rid, ha='center', va='center', fontsize=6.5,
            fontweight='bold', color='#CC0000')
    # Name
    ax.text(lx + 0.3, y, name, ha='left', va='center', fontsize=8.5,
            color='#333333')


# ===== COLOR LEGEND =====
cly = 2.5
ax.text(lx, cly + 0.4, 'Уровень риска', fontsize=10, fontweight='bold',
        color='#333333')

levels = [
    (LOW, 'Низкий — мониторинг'),
    (MED, 'Средний — плановые меры'),
    (HIGH, 'Высокий — активная митигация'),
    (CRIT, 'Критический — эскалация'),
]

for idx, (color, name) in enumerate(levels):
    y = cly - idx * 0.35
    rect = Rectangle((lx - 0.05, y - 0.12), 0.3, 0.24, facecolor=color,
                     edgecolor='#333333', linewidth=0.8, alpha=0.5)
    ax.add_patch(rect)
    ax.text(lx + 0.4, y, name, ha='left', va='center', fontsize=8.5,
            color='#333333')


plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig11_Risk_Matrix.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
