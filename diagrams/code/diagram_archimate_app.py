import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(18, 12))
ax.set_xlim(0, 18)
ax.set_ylim(0, 12)
ax.axis('off')
fig.patch.set_facecolor('white')

# ===== COLORS (ArchiMate standard) =====
APP_FILL = '#DAE8FC'       # application components - blue
APP_BORDER = '#6C8EBF'
DATA_FILL = '#D5E8D4'      # data objects - green
DATA_BORDER = '#82B366'
BIZ_FILL = '#FFF2CC'       # business actors - yellow
BIZ_BORDER = '#D6B656'
INFRA_FILL = '#E1D5E7'     # infrastructure - purple
INFRA_BORDER = '#9673A6'
NEW_FILL = '#DCEEFA'       # new system boundary
NEW_BORDER = '#3A7BBF'
ARROW_COLOR = '#555555'
FLOW_COLOR = '#4A90D9'

EM = '\u2014'


def draw_box(x, y, w, h, fill, border, text_lines, fontsize=9, bold=False, lw=1.5):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.06",
                          facecolor=fill, edgecolor=border, linewidth=lw)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    n = len(text_lines)
    for i, line in enumerate(text_lines):
        offset = (n - 1) / 2 - i
        ax.text(x + w/2, y + h/2 + offset * 0.24, line,
                ha='center', va='center', fontsize=fontsize,
                fontweight=weight, color='#333333')


def draw_arrow(x1, y1, x2, y2, color=ARROW_COLOR, lw=1.3, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw, linestyle=ls))


def draw_flow_arrow(x1, y1, x2, y2, color=FLOW_COLOR, lw=1.5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))


def draw_line_then_arrow(points, color=FLOW_COLOR, lw=1.3):
    for i in range(len(points) - 2):
        ax.plot([points[i][0], points[i+1][0]], [points[i][1], points[i+1][1]],
                color=color, linewidth=lw)
    ax.annotate('', xy=points[-1], xytext=points[-2],
                arrowprops=dict(arrowstyle='->', color=color, lw=lw))


# ===== TITLE =====
ax.text(9, 11.6, 'ArchiMate Application Cooperation View (TO-BE)',
        ha='center', va='center', fontsize=14, fontweight='bold', color='#333333')
ax.text(9, 11.25, 'Программные компоненты информационно-аналитической системы и их взаимодействие',
        ha='center', va='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== EXTERNAL DATA SOURCES (left) =====
ax.text(1.5, 10.1, 'Внешние источники', ha='center', va='center',
        fontsize=10, fontweight='bold', color=BIZ_BORDER)

draw_box(0.3, 8.9, 2.4, 0.9, BIZ_FILL, BIZ_BORDER,
         ['OMS', '(Система управления', 'заказами)'], fontsize=8.5, bold=True)

draw_box(0.3, 7.5, 2.4, 0.9, BIZ_FILL, BIZ_BORDER,
         ['Telegram', '(Чаты курьеров)'], fontsize=8.5, bold=True)

# ===== NEW SYSTEM BOUNDARY =====
sys_box = FancyBboxPatch((3.3, 1.5), 11.4, 9.0,
                          boxstyle="round,pad=0.15",
                          facecolor='#F8FBFF', edgecolor=NEW_BORDER,
                          linewidth=2.5, linestyle='--', alpha=0.6)
ax.add_patch(sys_box)
ax.text(9, 10.2, 'Информационно-аналитическая система (ИАС)',
        ha='center', va='center', fontsize=12, fontweight='bold', color=NEW_BORDER)

# ===== DATA COLLECTION LAYER =====
ax.text(5.5, 9.3, 'Сбор данных', ha='center', va='center',
        fontsize=9, fontweight='bold', color=DATA_BORDER, fontstyle='italic')

draw_box(4.0, 8.3, 3.0, 0.8, APP_FILL, APP_BORDER,
         ['OMS Data Connector', '(REST API / SQL)'], fontsize=8.5, bold=True)

draw_box(4.0, 7.1, 3.0, 0.8, APP_FILL, APP_BORDER,
         ['Telegram Bot', '(Bot API, парсинг)'], fontsize=8.5, bold=True)

# Arrows: sources -> connectors
draw_flow_arrow(2.7, 9.35, 4.0, 8.7)
draw_flow_arrow(2.7, 7.95, 4.0, 7.5)

# ===== DATA STORAGE =====
draw_box(4.0, 5.5, 3.0, 1.0, DATA_FILL, DATA_BORDER,
         ['Хранилище данных', '(Data Lake)', 'PostgreSQL + MinIO'], fontsize=8.5, bold=True)

# Arrows: connectors -> storage
draw_flow_arrow(5.5, 8.3, 5.5, 6.5)
draw_flow_arrow(5.5, 7.1, 5.5, 6.5)

# Data labels
ax.text(4.9, 7.8, 'отзывы, оценки', fontsize=7, color='#888888', fontstyle='italic')
ax.text(4.9, 6.9, 'сообщения', fontsize=7, color='#888888', fontstyle='italic')

# ===== LLM PROCESSING PIPELINE (center) =====
ax.text(10.5, 9.3, 'Обработка (LLM Pipeline)', ha='center', va='center',
        fontsize=9, fontweight='bold', color=APP_BORDER, fontstyle='italic')

draw_box(8.5, 8.2, 2.8, 0.9, APP_FILL, APP_BORDER,
         ['Препроцессор', '(очистка, нормализация,', 'auto-batching)'], fontsize=8, bold=True)

draw_box(8.5, 6.8, 2.8, 0.9, APP_FILL, APP_BORDER,
         ['LLM Engine', '(Map: анализ пакетов)'], fontsize=8.5, bold=True)

draw_box(8.5, 5.3, 2.8, 0.9, APP_FILL, APP_BORDER,
         ['Агрегатор', '(Reduce: синтез', 'итогового отчёта)'], fontsize=8, bold=True)

# LLM Model box (to the right of LLM Engine)
draw_box(12.0, 6.8, 2.5, 0.9, INFRA_FILL, INFRA_BORDER,
         ['LLM Model', '(DeepSeek / Qwen /', 'GPT-3.5 / YandexGPT)'], fontsize=7.5, bold=True)

# Arrows within pipeline
draw_flow_arrow(7.0, 6.0, 8.5, 6.0)
ax.text(7.75, 6.2, 'сырые\nданные', fontsize=7, color='#888888',
        ha='center', fontstyle='italic')

draw_flow_arrow(9.9, 8.2, 9.9, 7.7)
draw_flow_arrow(9.9, 6.8, 9.9, 6.2)

# Storage -> Preprocessor
draw_line_then_arrow([(5.5, 5.5), (5.5, 4.8), (8.0, 4.8), (8.0, 8.65), (8.5, 8.65)],
                     color=FLOW_COLOR, lw=1.2)

# LLM Engine <-> LLM Model
draw_flow_arrow(11.3, 7.25, 12.0, 7.25)
draw_arrow(12.0, 7.1, 11.3, 7.1, color=INFRA_BORDER, lw=1, ls='--')
ax.text(11.65, 7.5, 'промпт', fontsize=7, color='#888888', fontstyle='italic')
ax.text(11.65, 6.9, 'ответ', fontsize=7, color='#888888', fontstyle='italic')

# ===== RESULTS STORAGE =====
draw_box(8.5, 3.8, 2.8, 0.9, DATA_FILL, DATA_BORDER,
         ['Результаты анализа', '(аналитическая БД)', 'PostgreSQL'], fontsize=8, bold=True)

draw_flow_arrow(9.9, 5.3, 9.9, 4.7)
ax.text(10.2, 5.0, 'инсайты, тональность,\nтемы, суммаризация',
        fontsize=7, color='#888888', fontstyle='italic')

# ===== VISUALIZATION / OUTPUT =====
ax.text(9, 2.8, 'Представление', ha='center', va='center',
        fontsize=9, fontweight='bold', color=APP_BORDER, fontstyle='italic')

draw_box(4.5, 1.8, 3.0, 0.8, APP_FILL, APP_BORDER,
         ['Аналитический дашборд', '(интерактивная визуализация)'], fontsize=8.5, bold=True)

draw_box(8.5, 1.8, 3.0, 0.8, APP_FILL, APP_BORDER,
         ['REST API', '(интеграция с внешними', 'системами)'], fontsize=8, bold=True)

draw_box(12.5, 1.8, 2.5, 0.8, APP_FILL, APP_BORDER,
         ['Уведомления', '(алерты, e-mail)'], fontsize=8.5, bold=True)

# Arrows: results -> outputs
draw_line_then_arrow([(9.9, 3.8), (9.9, 3.2), (6.0, 3.2), (6.0, 2.6)])
draw_flow_arrow(9.9, 3.8, 9.9, 2.6)
draw_line_then_arrow([(9.9, 3.8), (9.9, 3.2), (13.75, 3.2), (13.75, 2.6)])

# ===== USERS (bottom) =====
ax.text(9, 0.9, 'Пользователи', ha='center', va='center',
        fontsize=9, fontweight='bold', color=BIZ_BORDER, fontstyle='italic')

users = [
    (2.5, 'Менеджер'),
    (6.0, 'Руководитель'),
    (10.0, 'Продуктовая\nкоманда'),
    (13.75, 'Логистика'),
]

for ux, label in users:
    draw_box(ux - 1.0, 0.2, 2.0, 0.5, BIZ_FILL, BIZ_BORDER,
             label.split('\n'), fontsize=8, bold=True)

# Arrows from dashboard/api to users
for ux, _ in users:
    draw_arrow(ux, 1.8, ux, 0.7, color='#999999', lw=0.8, ls='--')

# ===== LEGEND =====
ly = -0.4
ax.text(1.0, ly, 'Легенда:', fontsize=8, fontweight='bold', color='#333333')

legend_items = [
    (APP_FILL, APP_BORDER, 'Программный компонент'),
    (DATA_FILL, DATA_BORDER, 'Хранилище данных'),
    (BIZ_FILL, BIZ_BORDER, 'Внешний субъект / Источник'),
    (INFRA_FILL, INFRA_BORDER, 'Инфраструктура (модель)'),
]

for i, (fill, border, label) in enumerate(legend_items):
    lx = 2.8 + i * 3.8
    box = FancyBboxPatch((lx, ly - 0.15), 0.5, 0.3,
                          boxstyle="round,pad=0.02",
                          facecolor=fill, edgecolor=border, linewidth=1.2)
    ax.add_patch(box)
    ax.text(lx + 0.65, ly, label, fontsize=7.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig4_ArchiMate_App.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
