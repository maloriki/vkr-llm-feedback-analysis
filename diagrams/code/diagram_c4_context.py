import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')
fig.patch.set_facecolor('white')

SYS_FILL = '#438DD5'
SYS_BORDER = '#2E6DA4'
SYS_TEXT = '#FFFFFF'
PERSON_FILL = '#08427B'
PERSON_BORDER = '#063059'
PERSON_TEXT = '#FFFFFF'
EXT_FILL = '#999999'
EXT_BORDER = '#6B6B6B'
EXT_TEXT = '#FFFFFF'
ARROW_COLOR = '#707070'


def draw_person(x, y, name, desc, fill=PERSON_FILL, border=PERSON_BORDER):
    # Head
    head = plt.Circle((x, y + 0.6), 0.3, fill=True,
                       facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(head)
    # Body
    body = FancyBboxPatch((x - 0.7, y - 0.5), 1.4, 1.0,
                           boxstyle="round,pad=0.08",
                           facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(body)
    ax.text(x, y + 0.05, name, ha='center', va='center',
            fontsize=9, fontweight='bold', color=PERSON_TEXT)
    ax.text(x, y - 0.25, desc, ha='center', va='center',
            fontsize=7, color='#CCCCCC', fontstyle='italic')


def draw_system(x, y, w, h, name, desc, fill=SYS_FILL, border=SYS_BORDER, text_color=SYS_TEXT):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.1",
                          facecolor=fill, edgecolor=border, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y + 0.25, name, ha='center', va='center',
            fontsize=12, fontweight='bold', color=text_color)
    # Multi-line description
    lines = desc.split('\n')
    for i, line in enumerate(lines):
        ax.text(x, y - 0.15 - i * 0.3, line, ha='center', va='center',
                fontsize=8, color='#CCDDEE', fontstyle='italic')


def draw_ext_system(x, y, w, h, name, desc, fill=EXT_FILL, border=EXT_BORDER):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=fill, edgecolor=border, linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y + 0.2, name, ha='center', va='center',
            fontsize=9, fontweight='bold', color=EXT_TEXT)
    ax.text(x, y - 0.15, desc, ha='center', va='center',
            fontsize=7, color='#DDDDDD', fontstyle='italic')


def draw_labeled_arrow(x1, y1, x2, y2, label, label_offset=(0, 0.2)):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=ARROW_COLOR, lw=1.3))
    mx = (x1 + x2) / 2 + label_offset[0]
    my = (y1 + y2) / 2 + label_offset[1]
    ax.text(mx, my, label, ha='center', va='center',
            fontsize=7.5, color='#555555', fontstyle='italic',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='#CCCCCC', alpha=0.9))


# ===== TITLE =====
ax.text(8, 11.6, 'C4 Context Diagram',
        ha='center', va='center', fontsize=15, fontweight='bold', color='#333333')
ax.text(8, 11.2, 'Информационно-аналитическая система анализа обратной связи',
        ha='center', va='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== CENTRAL SYSTEM =====
draw_system(8, 5.5, 4.5, 2.5,
            'ИАС анализа',
            'Автоматизированная система\nанализа обратной связи\nна основе LLM (MapReduce)')

# ===== USERS (top) =====
draw_person(3, 10, 'Менеджер', 'Просмотр инсайтов')
draw_person(7, 10, 'Руководитель', 'Стратег. решения')
draw_person(11, 10, 'Продукт. команда', 'UX-проблемы')
draw_person(14.5, 10, 'Логистика', 'Операц. проблемы')

# Arrows: users -> system
draw_labeled_arrow(3, 9.5, 6.5, 6.75, 'Просмотр дашборда,\nполучение алертов', (-0.5, 0.3))
draw_labeled_arrow(7, 9.5, 7.5, 6.75, 'Аналитические\nотчёты', (-0.4, 0.2))
draw_labeled_arrow(11, 9.5, 9.5, 6.75, 'Анализ UX-\nпроблем', (0.3, 0.2))
draw_labeled_arrow(14.5, 9.5, 10.0, 6.75, 'Мониторинг\nкурьеров', (0.6, 0.3))

# ===== EXTERNAL SYSTEMS (bottom & sides) =====

# OMS (left-bottom)
draw_ext_system(2.5, 3.0, 3.0, 1.2,
                'OMS', 'Система управления\nзаказами')
draw_labeled_arrow(4.0, 3.6, 5.75, 5.0, 'Отзывы, оценки\n(REST API / SQL)', (0, 0.3))

# Telegram (right-bottom)
draw_ext_system(13.5, 3.0, 3.0, 1.2,
                'Telegram', 'Мессенджер\n(чаты курьеров)')
draw_labeled_arrow(12.0, 3.6, 10.25, 5.0, 'Сообщения курьеров\n(Bot API)', (0, 0.3))

# Email / Notification (bottom center)
draw_ext_system(8, 1.5, 3.0, 1.0,
                'Email / Мессенджер', 'Каналы уведомлений')
draw_labeled_arrow(8, 4.25, 8, 2.0, 'Алерты, отчёты\n(SMTP / API)', (1.2, 0))

# ===== LEGEND =====
ly = 0.3
ax.text(1.0, ly, 'Легенда:', fontsize=8, fontweight='bold', color='#333333')

# Person
head_l = plt.Circle((2.2, ly + 0.15), 0.12, fill=True,
                     facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1)
ax.add_patch(head_l)
body_l = FancyBboxPatch((1.9, ly - 0.2), 0.6, 0.3,
                         boxstyle="round,pad=0.03",
                         facecolor=PERSON_FILL, edgecolor=PERSON_BORDER, linewidth=1)
ax.add_patch(body_l)
ax.text(2.8, ly, 'Пользователь', fontsize=7.5, va='center', color='#333333')

# System
sys_l = FancyBboxPatch((4.5, ly - 0.15), 0.6, 0.3,
                        boxstyle="round,pad=0.03",
                        facecolor=SYS_FILL, edgecolor=SYS_BORDER, linewidth=1)
ax.add_patch(sys_l)
ax.text(5.3, ly, 'Целевая система', fontsize=7.5, va='center', color='#333333')

# External
ext_l = FancyBboxPatch((7.3, ly - 0.15), 0.6, 0.3,
                        boxstyle="round,pad=0.03",
                        facecolor=EXT_FILL, edgecolor=EXT_BORDER, linewidth=1)
ax.add_patch(ext_l)
ax.text(8.1, ly, 'Внешняя система', fontsize=7.5, va='center', color='#333333')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig6_C4_Context.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
