"""
BPMN TO-BE — waterfall-компоновка.

Горизонтальные swim lanes, поток процесса идёт сверху вниз:
сбор данных → LLM-конвейер → дашборд → пользователь.
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

COLORS = {
    'auto':  ('#D5E8D4', '#82B366'),
    'llm':   ('#DAE8FC', '#6C8EBF'),
    'dash':  ('#E1D5E7', '#9673A6'),
    'user':  ('#FFF2CC', '#D6B656'),
}
ARROW = '#333333'
TIMER = '#E6882A'
END_COLOR = '#CC0000'
GATEWAY_FILL = '#FFF2CC'
GATEWAY_BORDER = '#D6B656'
IMPROVE = '#2E7D32'
LANE_BORDER = '#999999'
EN = '\u2013'

POOL_X = 0.3
POOL_W = 1.4
LANES_X = POOL_X + POOL_W
LANES_W = 17.3

# Порядок дорожек сверху вниз:
# 1. Сбор данных
# 2. LLM-конвейер
# 3. Дашборд
# 4. Пользователь
LANES = [
    ('auto', 'Сбор данных\n(автомат.)',       '#F5FCF5', 9.0, 1.8),
    ('llm',  'LLM-конвейер\n(автомат.)',      '#F7F9FD', 6.7, 1.8),
    ('dash', 'Дашборд\n(автомат.)',           '#FAF5FE', 4.6, 1.6),
    ('user', 'Менеджер /\nРуководитель',      '#FEFAF5', 2.6, 1.6),
]

BH = 0.7


def draw_pool_and_lanes():
    lane_top = LANES[0][3] + LANES[0][4] / 2
    lane_bot = LANES[-1][3] - LANES[-1][4] / 2
    pool = FancyBboxPatch((POOL_X, lane_bot), POOL_W, lane_top - lane_bot,
                          boxstyle="square,pad=0",
                          facecolor='#E8E8E8', edgecolor=LANE_BORDER, linewidth=1.5)
    ax.add_patch(pool)
    ax.text(POOL_X + POOL_W / 2, (lane_top + lane_bot) / 2,
            'Процесс анализа\nобратной связи\n(TO-BE)',
            ha='center', va='center', fontsize=9, fontweight='bold',
            color='#333333', rotation=90)

    for role, label, color, y, h in LANES:
        lane = FancyBboxPatch((LANES_X, y - h/2), LANES_W, h,
                              boxstyle="square,pad=0",
                              facecolor=color, edgecolor=LANE_BORDER, linewidth=0.8)
        ax.add_patch(lane)
        ax.text(LANES_X + 0.7, y, label,
                ha='center', va='center', fontsize=9, fontweight='bold',
                color='#555555')


def lane_y(key):
    for role, _, _, y, _ in LANES:
        if role == key:
            return y


def task(x, y, w, lines, role, fs=9):
    fill, border = COLORS[role]
    box = FancyBboxPatch((x - w/2, y - BH/2), w, BH,
                         boxstyle="round,pad=0.06",
                         facecolor=fill, edgecolor=border, linewidth=1.4)
    ax.add_patch(box)
    n = len(lines)
    for i, line in enumerate(lines):
        off = (n - 1) / 2 - i
        ax.text(x, y + off * 0.22, line,
                ha='center', va='center', fontsize=fs, color='#333333')


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


def gateway(x, y, s=0.3, kind='X'):
    if kind == '+':
        fill = '#E8F5E9'
        border = IMPROVE
        color = IMPROVE
    else:
        fill = GATEWAY_FILL
        border = GATEWAY_BORDER
        color = GATEWAY_BORDER
    d = plt.Polygon([(x, y+s), (x+s, y), (x, y-s), (x-s, y)],
                    fill=True, facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(d)
    ax.text(x, y, kind, ha='center', va='center', fontsize=12,
            fontweight='bold', color=color)


def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=ARROW, lw=1.3))


def connect_down(x1, y1_lane, x2, y2_lane):
    out_y = y1_lane - BH/2
    in_y = y2_lane + BH/2
    if abs(x1 - x2) < 0.01:
        arrow(x1, out_y, x2, in_y)
    else:
        mid_y = (out_y + in_y) / 2
        ax.plot([x1, x1], [out_y, mid_y], color=ARROW, linewidth=1.3)
        ax.plot([x1, x2], [mid_y, mid_y], color=ARROW, linewidth=1.3)
        arrow(x2, mid_y, x2, in_y)


# ===== TITLE =====
ax.text(9, 10.5, 'Модель бизнес-процесса TO-BE',
        ha='center', fontsize=14, fontweight='bold', color='#333333')
ax.text(9, 10.15,
        'Нотация BPMN 2.0 | Внедрена ИАС на основе LLM | Процесс: сверху вниз (waterfall)',
        ha='center', fontsize=9.5, fontstyle='italic', color='#666666')

draw_pool_and_lanes()

# ===== FLOW =====
# Lane auto (y=9.0): параллельный сбор данных
y_auto = lane_y('auto')

# Start timer
sx = 3.2
start_event(sx, y_auto, timer=True)
ax.text(sx, y_auto + 0.7, 'По расписанию', ha='center',
        fontsize=8, color=TIMER, fontstyle='italic')

# Parallel split
gw1_x = 4.2
gateway(gw1_x, y_auto, kind='+')
arrow(sx + 0.22, y_auto, gw1_x - 0.3, y_auto)

# Верхняя ветка: OMS
t1x = 6.5
task(t1x, y_auto + 0.5, 2.5, ['Автомат. выгрузка', 'из OMS'], 'auto')
ax.plot([gw1_x, gw1_x], [y_auto + 0.3, y_auto + 0.5], color=ARROW, linewidth=1.3)
ax.plot([gw1_x, t1x - 1.25], [y_auto + 0.5, y_auto + 0.5], color=ARROW, linewidth=1.3)
arrow(t1x - 1.25, y_auto + 0.5, t1x - 1.25, y_auto + 0.5 + 0.01)

# Нижняя ветка: Telegram
task(t1x, y_auto - 0.5, 2.5, ['Сбор сообщений', 'Telegram Bot'], 'auto')
ax.plot([gw1_x, gw1_x], [y_auto - 0.3, y_auto - 0.5], color=ARROW, linewidth=1.3)
ax.plot([gw1_x, t1x - 1.25], [y_auto - 0.5, y_auto - 0.5], color=ARROW, linewidth=1.3)
arrow(t1x - 1.25, y_auto - 0.5, t1x - 1.25, y_auto - 0.5 + 0.01)

# Parallel join
gw2_x = 9.0
gateway(gw2_x, y_auto, kind='+')
ax.plot([t1x + 1.25, gw2_x], [y_auto + 0.5, y_auto + 0.5], color=ARROW, linewidth=1.3)
ax.plot([gw2_x, gw2_x], [y_auto + 0.5, y_auto + 0.3], color=ARROW, linewidth=1.3)
ax.plot([t1x + 1.25, gw2_x], [y_auto - 0.5, y_auto - 0.5], color=ARROW, linewidth=1.3)
ax.plot([gw2_x, gw2_x], [y_auto - 0.5, y_auto - 0.3], color=ARROW, linewidth=1.3)

# NEW note
ax.text(t1x, y_auto - 1.1,
        'НОВОЕ: Telegram включён в анализ',
        ha='center', fontsize=8, color=IMPROVE, fontweight='bold',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#E8F5E9',
                  edgecolor=IMPROVE, linewidth=0.8, linestyle='dashed'))

# ===== LLM lane (y=6.7) =====
y_llm = lane_y('llm')

# T1: Preprocessing
t_pre_x = 4.5
task(t_pre_x, y_llm + 0.4, 2.4, ['Препроцессинг,', 'пакетирование'], 'llm')
connect_down(gw2_x, y_auto, t_pre_x, y_llm + 0.4)

# T2: LLM Map
t_map_x = 8.0
task(t_map_x, y_llm + 0.4, 2.6, ['LLM-анализ (Map):', 'темы, инсайты'], 'llm')
arrow(t_pre_x + 1.2, y_llm + 0.4, t_map_x - 1.3, y_llm + 0.4)

# T3: LLM Reduce
t_red_x = 11.5
task(t_red_x, y_llm + 0.4, 2.4, ['Агрегация (Reduce):', 'итоговый отчёт'], 'llm')
arrow(t_map_x + 1.3, y_llm + 0.4, t_red_x - 1.2, y_llm + 0.4)

# T4: Save DB
t_db_x = 14.7
task(t_db_x, y_llm + 0.4, 2.2, ['Сохранение', 'в БД'], 'llm')
arrow(t_red_x + 1.2, y_llm + 0.4, t_db_x - 1.1, y_llm + 0.4)

# Semantic note
ax.text(8.0, y_llm - 0.5,
        'Семантический анализ вместо ключевых слов',
        ha='center', fontsize=8, color=IMPROVE, fontweight='bold',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#E8F5E9',
                  edgecolor=IMPROVE, linewidth=0.8, linestyle='dashed'))

# ===== Dashboard lane (y=4.6) =====
y_dash = lane_y('dash')

# T5: Dashboard update
t_upd_x = 5.5
task(t_upd_x, y_dash, 2.5, ['Обновление', 'дашборда'], 'dash')
connect_down(t_db_x, y_llm + 0.4, t_upd_x, y_dash)

# T6: Alerts
t_alert_x = 9.0
task(t_alert_x, y_dash, 2.5, ['Автоматические', 'уведомления (алерты)'], 'dash')
arrow(t_upd_x + 1.25, y_dash, t_alert_x - 1.25, y_dash)

# Note
ax.text(13.5, y_dash,
        'НОВОЕ: drill-down,\nтренды, карта проблем',
        ha='center', fontsize=8, color=IMPROVE, fontweight='bold',
        fontstyle='italic',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#E8F5E9',
                  edgecolor=IMPROVE, linewidth=0.8, linestyle='dashed'))

# ===== User lane (y=2.6) =====
y_user = lane_y('user')

# T7: View insights
t_view_x = 5.5
task(t_view_x, y_user, 2.5, ['Просмотр инсайтов', 'и рекомендаций'], 'user')
connect_down(t_alert_x, y_dash, t_view_x, y_user)

# T8: Decide
t_dec_x = 9.0
task(t_dec_x, y_user, 2.5, ['Принятие решений', 'на основе инсайтов'], 'user')
arrow(t_view_x + 1.25, y_user, t_dec_x - 1.25, y_user)

# Gateway
gw_end_x = 11.8
gateway(gw_end_x, y_user)
arrow(t_dec_x + 1.25, y_user, gw_end_x - 0.3, y_user)
ax.text(gw_end_x, y_user + 0.45, 'Действие?', ha='center',
        fontsize=8, color='#666666', fontstyle='italic')

# End
end_x = 13.2
end_event(end_x, y_user)
arrow(gw_end_x + 0.3, y_user, end_x - 0.22, y_user)
ax.text((gw_end_x + end_x) / 2, y_user + 0.25, 'Нет',
        ha='center', fontsize=7.5, color='#555555')

# Yes loop back
ax.plot([gw_end_x, gw_end_x], [y_user + 0.3, y_user + BH/2 + 0.4],
        color=ARROW, linewidth=1.3)
ax.plot([gw_end_x, t_dec_x], [y_user + BH/2 + 0.4, y_user + BH/2 + 0.4],
        color=ARROW, linewidth=1.3)
arrow(t_dec_x, y_user + BH/2 + 0.4, t_dec_x, y_user + BH/2)
ax.text(gw_end_x - 0.15, y_user + 0.5, 'Да', fontsize=7.5, color='#555555')

# ===== BOTTOM =====
ax.text(9, 1.4,
        f'Минуты вместо дней  |  OMS + Telegram  |  Семантический анализ (LLM)',
        ha='center', fontsize=10, fontweight='bold', color=IMPROVE,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9',
                  edgecolor=IMPROVE, alpha=0.85, linewidth=1.2))

# ===== LEGEND =====
ly = 0.5
ax.text(0.4, ly, 'Легенда:', fontsize=9, fontweight='bold', color='#333333')

items = [
    (2.0, COLORS['auto'], 'Автоматизация'),
    (4.5, COLORS['llm'], 'LLM-конвейер'),
    (7.2, COLORS['dash'], 'Дашборд'),
    (9.5, COLORS['user'], 'Пользователь'),
]
for bx, (fill, border), label in items:
    box = FancyBboxPatch((bx, ly - 0.15), 0.4, 0.3,
                         boxstyle="round,pad=0.02",
                         facecolor=fill, edgecolor=border, linewidth=1.2)
    ax.add_patch(box)
    ax.text(bx + 0.55, ly, label, fontsize=8.5, va='center', color='#333333')

start_event(12.0, ly, r=0.12, timer=True)
ax.text(12.25, ly, 'Таймер', fontsize=8.5, va='center', color='#333333')

gateway(13.7, ly, s=0.15, kind='+')
ax.text(13.95, ly, 'Параллель', fontsize=8.5, va='center', color='#333333')

gateway(15.4, ly, s=0.15)
ax.text(15.65, ly, 'Условие', fontsize=8.5, va='center', color='#333333')

end_event(16.7, ly, r=0.12)
ax.text(16.95, ly, 'Конец', fontsize=8.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig5_BPMN_TOBE.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
