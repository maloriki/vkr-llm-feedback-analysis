import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(18, 16))
ax.set_xlim(0, 18)
ax.set_ylim(0, 16)
ax.axis('off')
fig.patch.set_facecolor('white')

CONT_FILL = '#438DD5'
CONT_BORDER = '#2E6DA4'
DB_FILL = '#3B7FC4'
DB_BORDER = '#2A5F94'
EXT_FILL = '#999999'
EXT_BORDER = '#6B6B6B'
PERSON_FILL = '#08427B'
PERSON_BORDER = '#063059'
WHITE = '#FFFFFF'
REL_COLOR = '#707070'


def draw_container(x, y, w, h, name, tech, desc=''):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=CONT_FILL, edgecolor=CONT_BORDER, linewidth=1.5)
    ax.add_patch(box)
    cy = y + h / 2
    ax.text(x + w/2, cy + 0.28, name, ha='center', va='center',
            fontsize=9.5, fontweight='bold', color=WHITE)
    ax.text(x + w/2, cy, f'[{tech}]', ha='center', va='center',
            fontsize=7.5, color='#AACCEE', fontstyle='italic')
    if desc:
        ax.text(x + w/2, cy - 0.28, desc, ha='center', va='center',
                fontsize=7.5, color='#CCDDEE')
    return x, y, w, h


def draw_database(x, y, w, h, name, tech, desc=''):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.06",
                          facecolor=DB_FILL, edgecolor=DB_BORDER, linewidth=1.5)
    ax.add_patch(box)
    # cylinder top
    ell = matplotlib.patches.Ellipse((x + w/2, y + h), w * 0.85, 0.22,
                                      facecolor='#5A9FDF', edgecolor=DB_BORDER, linewidth=1.2)
    ax.add_patch(ell)
    cy = y + h / 2
    ax.text(x + w/2, cy + 0.2, name, ha='center', va='center',
            fontsize=9.5, fontweight='bold', color=WHITE)
    ax.text(x + w/2, cy - 0.05, f'[{tech}]', ha='center', va='center',
            fontsize=7.5, color='#AACCEE', fontstyle='italic')
    if desc:
        ax.text(x + w/2, cy - 0.28, desc, ha='center', va='center',
                fontsize=7.5, color='#CCDDEE')
    return x, y, w, h


def draw_ext(x, y, w, h, name, desc=''):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.06",
                          facecolor=EXT_FILL, edgecolor=EXT_BORDER, linewidth=1.3)
    ax.add_patch(box)
    cy = y + h / 2
    ax.text(x + w/2, cy + 0.12, name, ha='center', va='center',
            fontsize=9.5, fontweight='bold', color=WHITE)
    if desc:
        ax.text(x + w/2, cy - 0.15, desc, ha='center', va='center',
                fontsize=7, color='#DDDDDD', fontstyle='italic')


def draw_person(x, y, name):
    head = plt.Circle((x, y + 0.4), 0.2, fill=True,
                       facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1.3)
    ax.add_patch(head)
    body = FancyBboxPatch((x - 0.55, y - 0.3), 1.1, 0.65,
                           boxstyle="round,pad=0.05",
                           facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1.3)
    ax.add_patch(body)
    ax.text(x, y, name, ha='center', va='center',
            fontsize=8, fontweight='bold', color=WHITE)


def draw_rel(x1, y1, x2, y2, label='', label_pos=None):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=REL_COLOR, lw=1.2))
    if label:
        lx = label_pos[0] if label_pos else (x1 + x2) / 2
        ly = label_pos[1] if label_pos else (y1 + y2) / 2
        ax.text(lx, ly, label, ha='center', va='center',
                fontsize=6.5, color='#555555', fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                          edgecolor='#DDDDDD', alpha=0.95))


def draw_line_rel(points, label='', label_pos=None):
    for i in range(len(points) - 2):
        ax.plot([points[i][0], points[i+1][0]], [points[i][1], points[i+1][1]],
                color=REL_COLOR, linewidth=1.2)
    ax.annotate('', xy=points[-1], xytext=points[-2],
                arrowprops=dict(arrowstyle='->', color=REL_COLOR, lw=1.2))
    if label and label_pos:
        ax.text(label_pos[0], label_pos[1], label, ha='center', va='center',
                fontsize=6.5, color='#555555', fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                          edgecolor='#DDDDDD', alpha=0.95))


# ===== TITLE =====
ax.text(9, 15.5, 'C4 Container Diagram', ha='center', fontsize=15,
        fontweight='bold', color='#333333')
ax.text(9, 15.1, 'Контейнеры информационно-аналитической системы анализа обратной связи',
        ha='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== USERS (top row, y=13.5) =====
draw_person(4.5, 13.8, 'Менеджер')
draw_person(9, 13.8, 'Руководитель')
draw_person(13.5, 13.8, 'Аналитик')

# ===== SYSTEM BOUNDARY =====
boundary = FancyBboxPatch((1.5, 1.5), 15, 11.2,
                           boxstyle="round,pad=0.2",
                           facecolor='#F4F8FF', edgecolor='#3A7BBF',
                           linewidth=2, linestyle='--', alpha=0.4)
ax.add_patch(boundary)
ax.text(9, 12.4, 'ИАС анализа обратной связи', ha='center',
        fontsize=11, fontweight='bold', color='#3A7BBF')

# ===== EXTERNAL SYSTEMS (left column, x=0) =====
draw_ext(0, 9.5, 1.5, 0.9, 'OMS', 'Заказы')
draw_ext(0, 7.5, 1.5, 0.9, 'Telegram', 'Мессенджер')
draw_ext(16, 3.0, 1.8, 0.9, 'Email', 'SMTP')

# ===== LAYER 1: DATA COLLECTION (y=10.5) =====
# OMS Connector
draw_container(2.5, 10.2, 2.8, 1.0,
               'OMS Connector', 'Python, REST',
               'Извлечение отзывов')

# Telegram Bot
draw_container(2.5, 8.2, 2.8, 1.0,
               'Telegram Bot', 'Python, aiogram',
               'Парсинг сообщений')

# ===== LAYER 2: STORAGE (y=8, center) =====
draw_database(6.5, 9.0, 2.8, 1.0,
              'Data Lake', 'PostgreSQL + MinIO',
              'Сырые данные')

draw_database(6.5, 5.5, 2.8, 1.0,
              'Аналитическая БД', 'PostgreSQL',
              'Результаты')

# ===== LAYER 3: PROCESSING (y=8, right) =====
draw_container(10.5, 10.2, 2.8, 1.0,
               'LLM Pipeline', 'Python, FastAPI',
               'MapReduce, batching')

draw_container(10.5, 8.2, 2.8, 1.0,
               'LLM Model Server', 'vLLM / Ollama',
               'DeepSeek / Qwen')

# ===== LAYER 4: PRESENTATION (bottom, y=3) =====
draw_container(2.5, 3.0, 2.8, 1.0,
               'Web Dashboard', 'Streamlit',
               'Визуализация')

draw_container(6.5, 3.0, 2.8, 1.0,
               'REST API', 'FastAPI',
               'Интеграции')

draw_container(10.5, 3.0, 2.8, 1.0,
               'Notification Svc', 'Python',
               'Алерты, отчёты')

# ===== ARROWS =====

# External -> Connectors (horizontal, touching edges)
draw_rel(1.5, 9.95, 2.5, 10.7, 'REST API', (2.0, 10.5))
draw_rel(1.5, 7.95, 2.5, 8.7, 'Bot API', (2.0, 8.5))

# Connectors -> Data Lake (horizontal)
draw_rel(5.3, 10.7, 6.5, 9.8, 'Отзывы', (5.9, 10.4))
draw_rel(5.3, 8.7, 6.5, 9.2, 'Сообщения', (5.9, 8.8))

# Data Lake -> LLM Pipeline (horizontal)
draw_rel(9.3, 9.7, 10.5, 10.7, 'Пакеты данных', (9.9, 10.35))

# LLM Pipeline <-> Model Server (vertical, between them)
draw_rel(11.9, 10.2, 11.9, 9.2, 'Промпт', (12.35, 9.8))
draw_rel(11.5, 9.2, 11.5, 10.2, 'Ответ', (11.1, 9.8))

# LLM Pipeline -> Analytics DB
draw_line_rel([
    (10.5, 10.5),
    (9.8, 10.5),
    (9.8, 6.3),
    (9.3, 6.3),
], label='Результаты', label_pos=(10.15, 8.5))

# Analytics DB -> Dashboard
draw_line_rel([
    (6.5, 5.7),
    (3.9, 5.7),
    (3.9, 4.0),
], label='SQL', label_pos=(5.0, 5.9))

# Analytics DB -> REST API
draw_rel(7.9, 5.5, 7.9, 4.0, 'Данные', (8.3, 4.8))

# Analytics DB -> Notification
draw_line_rel([
    (9.3, 5.8),
    (11.9, 5.8),
    (11.9, 4.0),
], label='Триггеры', label_pos=(10.6, 6.0))

# Notification -> Email
draw_rel(13.3, 3.5, 16.0, 3.5, 'SMTP', (14.6, 3.75))

# Users -> Dashboard / API (from bottom of persons to top of system)
draw_line_rel([
    (4.5, 13.5),
    (4.5, 12.0),
    (3.9, 12.0),
    (3.9, 4.0),
], label='Дашборд', label_pos=(3.4, 8.0))

draw_line_rel([
    (9, 13.5),
    (9, 12.0),
    (7.9, 12.0),
    (7.9, 4.0),
], label='API / Дашборд', label_pos=(8.6, 8.0))

draw_line_rel([
    (13.5, 13.5),
    (13.5, 12.0),
    (11.9, 12.0),
    (11.9, 11.2),
], label='Управление', label_pos=(13.0, 11.6))


# ===== LAYER LABELS (right side) =====
label_x = 16.5
labels = [
    (10.7, 'Сбор данных'),
    (9.2, 'Хранение /\nОбработка'),
    (5.8, 'Хранение\nрезультатов'),
    (3.5, 'Представление'),
]
for ly, lt in labels:
    ax.text(label_x, ly, lt, ha='center', va='center',
            fontsize=8, fontweight='bold', color='#BBBBBB',
            fontstyle='italic')

# ===== LEGEND =====
ly = 0.6
ax.text(1.5, ly, 'Легенда:', fontsize=8, fontweight='bold', color='#333333')

items = [
    (3.0, CONT_FILL, CONT_BORDER, 'Контейнер'),
    (5.5, DB_FILL, DB_BORDER, 'Хранилище'),
    (8.0, EXT_FILL, EXT_BORDER, 'Внешняя система'),
]
for lx, fill, border, label in items:
    box = FancyBboxPatch((lx, ly - 0.15), 0.5, 0.3,
                          boxstyle="round,pad=0.03",
                          facecolor=fill, edgecolor=border, linewidth=1)
    ax.add_patch(box)
    ax.text(lx + 0.7, ly, label, fontsize=7.5, va='center', color='#333333')

# Person in legend
head_l = plt.Circle((11.0, ly + 0.1), 0.1, fill=True,
                     facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1)
ax.add_patch(head_l)
body_l = FancyBboxPatch((10.75, ly - 0.15), 0.5, 0.2,
                         boxstyle="round,pad=0.02",
                         facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1)
ax.add_patch(body_l)
ax.text(11.5, ly, 'Пользователь', fontsize=7.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig7_C4_Container.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
