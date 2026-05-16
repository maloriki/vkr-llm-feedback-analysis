import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(16, 11))
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis('off')
fig.patch.set_facecolor('white')

# ===== COLORS =====
BIZ_FILL = '#FFF2CC'
BIZ_BORDER = '#D6B656'
DATA_FILL = '#DAE8FC'
DATA_BORDER = '#6C8EBF'
GAP_FILL = '#F8CECC'
GAP_BORDER = '#B85450'
ARROW_COLOR = '#666666'
TITLE_COLOR = '#333333'


def draw_box(x, y, w, h, fill, border, text_lines, fontsize=9, bold=False):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.05",
                          facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    n = len(text_lines)
    for i, line in enumerate(text_lines):
        offset = (n - 1) / 2 - i
        ax.text(x + w/2, y + h/2 + offset * 0.22, line,
                ha='center', va='center', fontsize=fontsize,
                fontweight=weight, color='#333333')


def draw_arrow(x1, y1, x2, y2, color=ARROW_COLOR, lw=1.5, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, linestyle=ls))


def draw_dashed_arrow(x1, y1, x2, y2, color='#999999'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.0, linestyle='dashed'))


# ===== TITLE =====
ax.text(8, 10.6, 'Организационная модель (ArchiMate Organization View)',
        ha='center', va='center', fontsize=15, fontweight='bold', color=TITLE_COLOR)
ax.text(8, 10.25, 'AS-IS: фрагментированный анализ обратной связи между подразделениями',
        ha='center', va='center', fontsize=11, fontstyle='italic', color='#666666')

# ===== DATA SOURCES =====
ax.text(8, 9.7, 'Источники данных', ha='center', va='center',
        fontsize=11, fontweight='bold', color=DATA_BORDER)

draw_box(2.5, 8.8, 4.5, 0.7, DATA_FILL, DATA_BORDER,
         ['Клиентские отзывы', '(система управления заказами)'], fontsize=10, bold=True)

draw_box(9, 8.8, 4.5, 0.7, DATA_FILL, DATA_BORDER,
         ['Сообщения курьеров', '(Telegram-чаты)'], fontsize=10, bold=True)

# ===== GAP ZONE =====
gap_box = FancyBboxPatch((3, 7.0), 10, 1.3,
                          boxstyle="round,pad=0.1",
                          facecolor=GAP_FILL, edgecolor=GAP_BORDER,
                          linewidth=2, linestyle='dashed', alpha=0.4)
ax.add_patch(gap_box)

ax.text(8, 7.85, 'ЕДИНАЯ АНАЛИТИЧЕСКАЯ СИСТЕМА ОТСУТСТВУЕТ',
        ha='center', va='center', fontsize=12, fontweight='bold', color=GAP_BORDER)
ax.text(8, 7.4, 'Фрагментированный доступ / Дублирование усилий / Противоречивые выводы / Задержки',
        ha='center', va='center', fontsize=8.5, fontstyle='italic', color='#994444')

# ===== DEPARTMENTS =====
ax.text(8, 6.3, 'Подразделения компании', ha='center', va='center',
        fontsize=11, fontweight='bold', color=BIZ_BORDER)

dept_y = 4.4
dept_h = 1.6
dept_w = 3.2
gap_x = 0.35

# Product
x1 = 0.5
draw_box(x1, dept_y, dept_w, dept_h, BIZ_FILL, BIZ_BORDER,
         ['Продуктовое', 'управление'], fontsize=10, bold=True)
ax.text(x1 + dept_w/2, dept_y + 0.35,
        'UX-проблемы, жалобы\nна функциональность,\nдорожная карта',
        ha='center', va='center', fontsize=7.5, color='#666666', fontstyle='italic')

# Operations
x2 = x1 + dept_w + gap_x
draw_box(x2, dept_y, dept_w, dept_h, BIZ_FILL, BIZ_BORDER,
         ['Операционное', 'управление'], fontsize=10, bold=True)
ax.text(x2 + dept_w/2, dept_y + 0.35,
        'Качество сервиса,\nпоказатели доставки,\nповторяющиеся проблемы',
        ha='center', va='center', fontsize=7.5, color='#666666', fontstyle='italic')

# Logistics
x3 = x2 + dept_w + gap_x
draw_box(x3, dept_y, dept_w, dept_h, BIZ_FILL, BIZ_BORDER,
         ['Логистическое', 'подразделение'], fontsize=10, bold=True)
ax.text(x3 + dept_w/2, dept_y + 0.35,
        'Проблемы курьеров,\nмаршруты, координация\nскладских операций',
        ha='center', va='center', fontsize=7.5, color='#666666', fontstyle='italic')

# Leadership
x4 = x3 + dept_w + gap_x
draw_box(x4, dept_y, dept_w, dept_h, BIZ_FILL, BIZ_BORDER,
         ['Высшее', 'руководство'], fontsize=10, bold=True)
ax.text(x4 + dept_w/2, dept_y + 0.35,
        'Тренды тональности,\nстратегические\nрешения',
        ha='center', va='center', fontsize=7.5, color='#666666', fontstyle='italic')

# ===== ARROWS: data -> gap =====
draw_arrow(4.75, 8.8, 5.5, 8.3, color=DATA_BORDER)
draw_arrow(11.25, 8.8, 10.5, 8.3, color=DATA_BORDER)

# ===== ARROWS: departments -> gap (dashed) =====
centers = [x1 + dept_w/2, x2 + dept_w/2, x3 + dept_w/2, x4 + dept_w/2]
for cx in centers:
    draw_dashed_arrow(cx, dept_y + dept_h, cx, 7.0)

# ===== X marks between departments =====
for i in range(len(centers) - 1):
    cx1 = centers[i] + dept_w/2 - 0.2
    cx2 = centers[i+1] - dept_w/2 + 0.5
    mid_y = dept_y + dept_h/2
    ax.plot([cx1, cx2], [mid_y, mid_y],
            color='#CC0000', linewidth=1.5, linestyle='dotted')
    mx = (cx1 + cx2) / 2
    ax.text(mx, mid_y + 0.12, 'X', ha='center', va='center',
            fontsize=13, color='#CC0000', fontweight='bold')

# ===== MANUAL PROCESS =====
proc_y = 3.0
ax.text(8, proc_y + 0.9, 'Текущий процесс (ручной)', ha='center', va='center',
        fontsize=10, fontweight='bold', color='#666666')

steps = [
    ['Ручное', 'чтение'],
    ['Субъективная', 'категоризация'],
    ['Отчёт', 'в Excel'],
    ['Статичный отчёт', 'руководителю'],
]
step_xs = [2.0, 5.3, 8.7, 12.0]

for lines, sx in zip(steps, step_xs):
    draw_box(sx, proc_y - 0.1, 2.3, 0.7, '#F5F5F5', '#999999', lines, fontsize=8)

# Arrows between steps
draw_arrow(4.3, proc_y + 0.25, 5.3, proc_y + 0.25, color='#999999', lw=1.2)
draw_arrow(7.6, proc_y + 0.25, 8.7, proc_y + 0.25, color='#999999', lw=1.2)
draw_arrow(11.0, proc_y + 0.25, 12.0, proc_y + 0.25, color='#999999', lw=1.2)

# Time label
ax.text(8, proc_y - 0.55, '6\u20138 часов на 200\u2013500 отзывов',
        ha='center', va='center', fontsize=9, fontweight='bold',
        color='#CC0000',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF0F0',
                  edgecolor='#CC0000', alpha=0.8))

# ===== LEGEND =====
legend_y = 1.2
ax.text(1, legend_y + 0.5, 'Легенда:', fontsize=9, fontweight='bold', color='#333333')

legend_items = [
    (DATA_FILL, DATA_BORDER, 'Источник данных (Business Object)'),
    (BIZ_FILL, BIZ_BORDER, 'Подразделение (Business Actor)'),
    (GAP_FILL, GAP_BORDER, 'Выявленный разрыв / Проблема'),
]

for i, (fill, border, label) in enumerate(legend_items):
    lx = 1 + i * 4.8
    box = FancyBboxPatch((lx, legend_y - 0.15), 0.5, 0.3,
                          boxstyle="round,pad=0.02",
                          facecolor=fill, edgecolor=border, linewidth=1.2)
    ax.add_patch(box)
    ax.text(lx + 0.7, legend_y, label, fontsize=8, va='center', color='#333333')

# Dashed arrow legend
ax.annotate('', xy=(14.5, legend_y), xytext=(14, legend_y),
            arrowprops=dict(arrowstyle='->', color='#999999', lw=1, linestyle='dashed'))
ax.text(14.7, legend_y, 'Фрагментированный доступ', fontsize=8, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig1_Organization_View.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
