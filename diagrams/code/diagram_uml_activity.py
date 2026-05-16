import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(14, 20))
ax.set_xlim(0, 14)
ax.set_ylim(0, 20)
ax.axis('off')
fig.patch.set_facecolor('white')

ACT_FILL = '#DAE8FC'
ACT_BORDER = '#6C8EBF'
DEC_FILL = '#FFF2CC'
DEC_BORDER = '#D6B656'
NOTE_FILL = '#F5F5F5'
NOTE_BORDER = '#CCCCCC'
STORE_FILL = '#D5E8D4'
STORE_BORDER = '#82B366'
LLM_FILL = '#E1D5E7'
LLM_BORDER = '#9673A6'
REDUCE_FILL = '#FFE6CC'
REDUCE_BORDER = '#D79B00'
ALERT_FILL = '#F8CECC'
ALERT_BORDER = '#B85450'
FORK_COLOR = '#333333'
ARROW_COLOR = '#333333'

CX = 7.0  # center axis for all main flow


def draw_action(x, y, w, h, lines, fill=ACT_FILL, border=ACT_BORDER, fontsize=9):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(box)
    n = len(lines)
    for i, line in enumerate(lines):
        offset = (n - 1) / 2 - i
        ax.text(x, y + offset * 0.28, line,
                ha='center', va='center', fontsize=fontsize, color='#333333')


def draw_decision(x, y, size=0.35):
    diamond = plt.Polygon([
        (x, y + size), (x + size * 1.3, y), (x, y - size), (x - size * 1.3, y)
    ], fill=True, facecolor=DEC_FILL, edgecolor=DEC_BORDER, linewidth=1.5)
    ax.add_patch(diamond)


def draw_fork_bar(x, y, w):
    ax.plot([x - w/2, x + w/2], [y, y],
            color=FORK_COLOR, linewidth=5, solid_capstyle='round')


def draw_start(x, y):
    circle = plt.Circle((x, y), 0.2, fill=True,
                        facecolor='#333333', edgecolor='#333333', linewidth=2)
    ax.add_patch(circle)


def draw_end(x, y):
    outer = plt.Circle((x, y), 0.22, fill=False,
                       edgecolor='#333333', linewidth=2.5)
    inner = plt.Circle((x, y), 0.13, fill=True,
                       facecolor='#333333', edgecolor='#333333', linewidth=1)
    ax.add_patch(outer)
    ax.add_patch(inner)


def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=ARROW_COLOR, lw=1.3))


def line_arrow(points):
    for i in range(len(points) - 2):
        ax.plot([points[i][0], points[i+1][0]], [points[i][1], points[i+1][1]],
                color=ARROW_COLOR, linewidth=1.3)
    ax.annotate('', xy=points[-1], xytext=points[-2],
                arrowprops=dict(arrowstyle='->', color=ARROW_COLOR, lw=1.3))


def note(x, y, w, lines, fontsize=8):
    h = len(lines) * 0.25 + 0.15
    box = FancyBboxPatch((x, y - h/2), w, h,
                          boxstyle="round,pad=0.05",
                          facecolor=NOTE_FILL, edgecolor=NOTE_BORDER,
                          linewidth=0.8, linestyle='dashed')
    ax.add_patch(box)
    n = len(lines)
    for i, line in enumerate(lines):
        offset = (n - 1) / 2 - i
        ax.text(x + w/2, y + offset * 0.22, line,
                ha='center', va='center', fontsize=fontsize,
                color='#666666', fontstyle='italic')
    return x  # left edge for connecting line


# ===== TITLE =====
ax.text(CX, 19.5, 'UML Activity Diagram: LLM-конвейер обработки данных',
        ha='center', va='center', fontsize=13, fontweight='bold', color='#333333')
ax.text(CX, 19.1, 'Паттерн MapReduce с автоматическим подбором размера пакета',
        ha='center', va='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== VERTICAL FLOW (all on CX) =====

# START
sy = 18.5
draw_start(CX, sy)

# A1: Get data
a1 = 17.7
draw_action(CX, a1, 4.5, 0.7,
            ['Получение данных из Data Lake',
             '(отзывы OMS + сообщения Telegram)'])
arrow(CX, sy - 0.2, CX, a1 + 0.35)

# A2: Preprocessing
a2 = 16.7
draw_action(CX, a2, 4.5, 0.7,
            ['Предобработка текста',
             '(очистка, нормализация, дедупликация)'])
arrow(CX, a1 - 0.35, CX, a2 + 0.35)

note(10.5, a2, 2.5, ['Удаление HTML, emoji,', 'нормализация пробелов'], fontsize=7.5)
ax.plot([9.25, 10.5], [a2, a2], color=NOTE_BORDER, linewidth=0.8, linestyle='dashed')

# A3: Auto-batching
a3 = 15.5
draw_action(CX, a3, 4.5, 0.8,
            ['Автоматический подбор размера пакета',
             '(auto-batching)',
             'на основе контекстного окна модели'], fontsize=8.5)
arrow(CX, a2 - 0.35, CX, a3 + 0.4)

note(10.8, a3, 2.3, ['batch_size =', 'f(context_window,', 'avg_token_count)'], fontsize=7.5)
ax.plot([9.25, 10.8], [a3, a3], color=NOTE_BORDER, linewidth=0.8, linestyle='dashed')

# ===== LOOP BOX =====
loop_top = 14.4
loop_bot = 9.6
loop_l = 3.2
loop_r = 10.8

loop_box = FancyBboxPatch((loop_l, loop_bot), loop_r - loop_l, loop_top - loop_bot,
                           boxstyle="round,pad=0.12",
                           facecolor='#FAFAFF', edgecolor='#AAAACC',
                           linewidth=1.5, linestyle='--', alpha=0.5)
ax.add_patch(loop_box)
ax.text(loop_l + 0.2, loop_top - 0.15, 'loop [для каждого пакета]',
        fontsize=8, fontweight='bold', color='#666699', fontstyle='italic')

arrow(CX, a3 - 0.4, CX, loop_top)

# A4: Construct prompt
a4 = 13.7
draw_action(CX, a4, 4.0, 0.65,
            ['Формирование промпта',
             '(системная инструкция + данные пакета)'])
arrow(CX, loop_top, CX, a4 + 0.325)

# A5: Send to LLM
a5 = 12.7
draw_action(CX, a5, 3.8, 0.6,
            ['Отправка запроса к LLM-модели'],
            fill=LLM_FILL, border=LLM_BORDER)
arrow(CX, a4 - 0.325, CX, a5 + 0.3)

note(10.5, a5, 2.5, ['DeepSeek V3 / Qwen 2.5 /', 'GPT-3.5 / YandexGPT'], fontsize=7.5)
ax.plot([8.9, 10.5], [a5, a5], color=NOTE_BORDER, linewidth=0.8, linestyle='dashed')

# A6: Parse response
a6 = 11.6
draw_action(CX, a6, 4.0, 0.7,
            ['Парсинг ответа LLM',
             '(тональность, темы, инсайты, резюме)'])
arrow(CX, a5 - 0.3, CX, a6 + 0.35)

# A7: Store intermediate (on center axis)
a7 = 10.5
draw_action(CX, a7, 3.5, 0.6,
            ['Сохранение промежуточных результатов'],
            fill=STORE_FILL, border=STORE_BORDER, fontsize=8.5)
arrow(CX, a6 - 0.35, CX, a7 + 0.3)

# Loop back arrow (down out of loop, then continues)
arrow(CX, a7 - 0.3, CX, loop_bot)

# ===== REDUCE PHASE =====

# A8: Aggregation
a8 = 8.7
draw_action(CX, a8, 4.5, 0.85,
            ['Агрегация результатов (Reduce)',
             'Синтез промежуточных анализов',
             'в итоговый отчёт'],
            fill=REDUCE_FILL, border=REDUCE_BORDER)
arrow(CX, loop_bot, CX, a8 + 0.425)

# A9: Generate report
a9 = 7.5
draw_action(CX, a9, 4.2, 0.7,
            ['Формирование итогового отчёта',
             '(тренды, топ проблем, рекомендации)'],
            fill=REDUCE_FILL, border=REDUCE_BORDER)
arrow(CX, a8 - 0.425, CX, a9 + 0.35)

# A10: Save to DB
a10 = 6.5
draw_action(CX, a10, 3.8, 0.6,
            ['Сохранение в аналитическую БД'],
            fill=STORE_FILL, border=STORE_BORDER)
arrow(CX, a9 - 0.35, CX, a10 + 0.3)

# Decision: critical changes?
dec = 5.5
draw_decision(CX, dec)
arrow(CX, a10 - 0.3, CX, dec + 0.35)

# Yes -> alert (right)
alert_x = 11.0
draw_action(alert_x, dec, 2.2, 0.55,
            ['Отправка алерта',
             '(email, мессенджер)'],
            fontsize=8, fill=ALERT_FILL, border=ALERT_BORDER)
arrow(CX + 0.45, dec, alert_x - 1.1, dec)
ax.text(CX + 0.7, dec + 0.25, 'Да', fontsize=8, color='#555555')

# No -> continue down
ax.text(CX - 0.4, dec - 0.5, 'Нет', fontsize=8, color='#555555')

# A11: Update dashboard
a11 = 4.3
draw_action(CX, a11, 3.8, 0.6,
            ['Обновление дашборда'],
            fill=LLM_FILL, border=LLM_BORDER)
arrow(CX, dec - 0.35, CX, a11 + 0.3)

# Alert also leads down to dashboard
line_arrow([(alert_x, dec - 0.275),
            (alert_x, a11),
            (CX + 1.9, a11)])

# FORK BAR
fork = 3.4
draw_fork_bar(CX, fork, 4.0)
arrow(CX, a11 - 0.3, CX, fork + 0.05)

# Branch left
b1x = 5.0
b1 = 2.4
draw_action(b1x, b1, 2.8, 0.55,
            ['Данные доступны', 'через REST API'],
            fontsize=8, fill=STORE_FILL, border=STORE_BORDER)
arrow(b1x, fork - 0.05, b1x, b1 + 0.275)

# Branch right
b2x = 9.0
b2 = 2.4
draw_action(b2x, b2, 2.8, 0.55,
            ['Отчёт доступен', 'в дашборде'],
            fontsize=8, fill=STORE_FILL, border=STORE_BORDER)
arrow(b2x, fork - 0.05, b2x, b2 + 0.275)

# JOIN BAR
join = 1.5
draw_fork_bar(CX, join, 4.0)
arrow(b1x, b1 - 0.275, b1x, join + 0.05)
arrow(b2x, b2 - 0.275, b2x, join + 0.05)

# END
draw_end(CX, 0.8)
arrow(CX, join - 0.05, CX, 1.02)

# ===== PHASE LABELS (left margin) =====
phases = [
    (17.2, 'ПОДГОТОВКА'),
    (15.5, 'BATCHING'),
    (12.0, 'MAP-ФАЗА'),
    (8.1, 'REDUCE-ФАЗА'),
    (4.5, 'ДОСТАВКА'),
]
for py, label in phases:
    ax.text(1.3, py, label, ha='center', va='center',
            fontsize=8, fontweight='bold', color='#AAAAAA',
            rotation=90, fontstyle='italic')
    # small line
    ax.plot([2.0, 2.3], [py, py], color='#DDDDDD', linewidth=0.5)

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig8_UML_Activity.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
