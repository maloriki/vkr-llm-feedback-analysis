import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(18, 11))

# ===== COLORS BY PHASE =====
COLORS = {
    'pilot':   '#E6B85A',
    'mvp':     '#6C8EBF',
    'deploy':  '#82B366',
    'scale':   '#9673A6',
    'full':    '#D79B00',
    'support': '#B85450',
}
PHASE_NAMES = {
    'pilot':   'Фаза 1. Пилот',
    'mvp':     'Фаза 2. MVP',
    'deploy':  'Фаза 3. Продуктивное развёртывание',
    'scale':   'Фаза 4. Масштабирование',
    'full':    'Фаза 5. Промышленная эксплуатация',
    'support': 'Поддержка и развитие',
}

# ===== TASKS: (name, phase, start_month, duration_months, critical) =====
TASKS = [
    # Phase 1: Pilot (месяцы 1-2)
    ('Анализ требований и проектирование', 'pilot', 0, 1, False),
    ('Реализация LLM-конвейера (MapReduce)', 'pilot', 0.5, 1.5, True),
    ('Интеграция с OMS (коннектор)', 'pilot', 1, 1, False),
    ('Базовый аналитический дашборд', 'pilot', 1.5, 1, False),

    # Phase 2: MVP (месяцы 3-4)
    ('Интеграция Telegram Bot', 'mvp', 2, 1, False),
    ('Расширение дашборда (детализация)', 'mvp', 2.5, 1.5, False),
    ('Система автоматических уведомлений', 'mvp', 3, 1, False),
    ('Обучение пользователей, документация', 'mvp', 3.5, 0.5, False),

    # Phase 3: Deployment (месяцы 5-6)
    ('Развёртывание на продуктивном сервере', 'deploy', 4, 0.75, True),
    ('Мониторинг качества, оптимизация промптов', 'deploy', 4.5, 1.5, True),
    ('A/B-тестирование (LLM vs текущий процесс)', 'deploy', 5, 1, False),

    # Phase 4: Scale (месяцы 7-9)
    ('Подключение команд: логистика', 'scale', 6, 1, False),
    ('Подключение команд: продукт', 'scale', 7, 1, False),
    ('Расширение источников данных', 'scale', 7.5, 1.5, False),
    ('Оптимизация инфраструктуры (GPU)', 'scale', 8, 1, False),

    # Phase 5: Production (месяцы 10-12)
    ('Промышленная эксплуатация', 'full', 9, 3, True),
    ('Мониторинг бизнес-KPI', 'full', 9.5, 2.5, False),

    # Support: весь период
    ('Поддержка и итеративное улучшение', 'support', 4, 8, False),
]

MILESTONES = [
    (2.0, 'MVP готов'),
    (4.0, 'Продуктив запущен'),
    (6.0, 'Пилот успешен'),
    (9.0, 'Масштабирование завершено'),
    (12.0, 'Полное внедрение'),
]

# ===== PLOTTING =====
n_tasks = len(TASKS)
y_positions = list(range(n_tasks, 0, -1))

for i, (name, phase, start, duration, critical) in enumerate(TASKS):
    y = y_positions[i]
    color = COLORS[phase]
    edge = 'black' if critical else '#555555'
    lw = 2 if critical else 1

    bar = FancyBboxPatch(
        (start, y - 0.35), duration, 0.7,
        boxstyle="round,pad=0.02",
        facecolor=color,
        edgecolor=edge,
        linewidth=lw,
        alpha=0.9
    )
    ax.add_patch(bar)

    # Task duration in center
    ax.text(start + duration/2, y,
            f'{int(duration*4)} нед.' if duration < 1 else f'{duration:.0f} мес.'.replace('.0', ''),
            ha='center', va='center', fontsize=8, color='white', fontweight='bold')

# ===== MILESTONES (diamonds) =====
for mx, mname in MILESTONES:
    ax.plot(mx, n_tasks + 1, marker='D', markersize=13,
            color='#CC0000', markeredgecolor='black', markeredgewidth=1.5,
            zorder=10)
    ax.text(mx, n_tasks + 1.6, mname, ha='center', fontsize=8.5,
            fontweight='bold', color='#CC0000', rotation=0)

# ===== Y AXIS (task names) =====
ax.set_yticks(y_positions)
ax.set_yticklabels([t[0] for t in TASKS], fontsize=9)

# ===== X AXIS (months) =====
ax.set_xticks(range(13))
ax.set_xticklabels([f'М{i}' if i > 0 else 'Старт' for i in range(13)], fontsize=9)
ax.set_xlim(-0.3, 12.3)
ax.set_ylim(-0.5, n_tasks + 2.8)

# Grid
ax.grid(True, axis='x', linestyle='--', alpha=0.3)
ax.set_axisbelow(True)

# Phase backgrounds
phase_bounds = [
    (0, 2, 'pilot'),
    (2, 4, 'mvp'),
    (4, 6, 'deploy'),
    (6, 9, 'scale'),
    (9, 12, 'full'),
]
for start, end, phase in phase_bounds:
    ax.axvspan(start, end, alpha=0.08, color=COLORS[phase], zorder=0)
    # Phase label at top
    ax.text((start + end) / 2, n_tasks + 2.3,
            PHASE_NAMES[phase].split('.')[0],
            ha='center', fontsize=9, fontweight='bold',
            color=COLORS[phase])

# Remove spines
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

# ===== TITLE =====
ax.set_title('Диаграмма Ганта: план внедрения информационно-аналитической системы',
             fontsize=13, fontweight='bold', pad=35)

ax.set_xlabel('Месяц проекта', fontsize=10, fontweight='bold')

# ===== LEGEND =====
legend_patches = [
    mpatches.Patch(color=COLORS['pilot'], label='Пилот (M1–M2)'),
    mpatches.Patch(color=COLORS['mvp'], label='MVP (M3–M4)'),
    mpatches.Patch(color=COLORS['deploy'], label='Развёртывание (M5–M6)'),
    mpatches.Patch(color=COLORS['scale'], label='Масштабирование (M7–M9)'),
    mpatches.Patch(color=COLORS['full'], label='Эксплуатация (M10–M12)'),
    mpatches.Patch(color=COLORS['support'], label='Поддержка'),
    plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='#CC0000',
               markeredgecolor='black', markersize=10, label='Контрольная точка'),
    mpatches.Patch(facecolor='white', edgecolor='black', linewidth=2,
                   label='Критический путь'),
]
ax.legend(handles=legend_patches, loc='lower right', ncol=2,
          fontsize=8, framealpha=0.95, title='Условные обозначения',
          title_fontsize=9)

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig10_Gantt.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
