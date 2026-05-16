import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Segoe UI']

fig, ax = plt.subplots(1, 1, figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('white')

HEADER_FILL = '#438DD5'
HEADER_BORDER = '#2E6DA4'
TABLE_FILL = '#F5F8FF'
TABLE_BORDER = '#8FAACC'
PK_COLOR = '#D4A017'
FK_COLOR = '#6C8EBF'
REL_COLOR = '#707070'


class Table:
    """Helper to track table position and edges."""
    def __init__(self, x, y, w, name, fields, pk_fields=None, fk_fields=None):
        self.x = x          # left edge
        self.y = y           # top edge
        self.w = w
        self.name = name
        self.fields = fields
        self.pk_fields = pk_fields or []
        self.fk_fields = fk_fields or []

        self.row_h = 0.3
        self.header_h = 0.42
        self.pad = 0.08
        self.h = self.header_h + len(fields) * self.row_h + self.pad
        self.bottom = y - self.h
        self.right = x + w
        self.cx = x + w / 2
        self.cy = y - self.h / 2

    def draw(self):
        # Body
        body = FancyBboxPatch((self.x, self.bottom), self.w, self.h,
                               boxstyle="round,pad=0.03",
                               facecolor=TABLE_FILL, edgecolor=TABLE_BORDER, linewidth=1.3)
        ax.add_patch(body)

        # Header
        header = FancyBboxPatch((self.x, self.y - self.header_h), self.w, self.header_h,
                                 boxstyle="round,pad=0.03",
                                 facecolor=HEADER_FILL, edgecolor=HEADER_BORDER, linewidth=1.3)
        ax.add_patch(header)
        ax.text(self.cx, self.y - self.header_h / 2, self.name,
                ha='center', va='center', fontsize=10, fontweight='bold', color='white')

        # Fields
        for i, (fname, ftype) in enumerate(self.fields):
            fy = self.y - self.header_h - (i + 0.5) * self.row_h - self.pad / 2
            color = '#333333'
            weight = 'normal'
            prefix = ''

            if fname in self.pk_fields:
                prefix = 'PK '
                color = PK_COLOR
                weight = 'bold'
            elif fname in self.fk_fields:
                prefix = 'FK '
                color = FK_COLOR
                weight = 'bold'

            ax.text(self.x + 0.12, fy, f'{prefix}{fname}',
                    ha='left', va='center', fontsize=8, fontweight=weight, color=color)
            ax.text(self.right - 0.12, fy, ftype,
                    ha='right', va='center', fontsize=7.5, color='#888888', fontstyle='italic')

            if i < len(self.fields) - 1:
                sep_y = fy - self.row_h / 2
                ax.plot([self.x + 0.04, self.right - 0.04], [sep_y, sep_y],
                        color='#E0E0E0', linewidth=0.5)

    def field_y(self, field_name):
        """Get y coordinate of a specific field."""
        for i, (fname, _) in enumerate(self.fields):
            if fname == field_name:
                return self.y - self.header_h - (i + 0.5) * self.row_h - self.pad / 2
        return self.cy

    def left_at(self, y):
        return self.x, y

    def right_at(self, y):
        return self.right, y

    def top_at(self, x):
        return x, self.y

    def bottom_at(self, x):
        return x, self.bottom


def draw_rel(points, card1='', card2=''):
    """Draw relationship line touching block edges, with cardinality."""
    for i in range(len(points) - 1):
        ax.plot([points[i][0], points[i+1][0]],
                [points[i][1], points[i+1][1]],
                color=REL_COLOR, linewidth=1.3, solid_capstyle='round')
    # Small diamonds at endpoints
    for pt in [points[0], points[-1]]:
        ax.plot(pt[0], pt[1], 'o', color=REL_COLOR, markersize=3)
    if card1:
        dx = points[1][0] - points[0][0]
        dy = points[1][1] - points[0][1]
        ox = 0.15 if dx > 0 else (-0.15 if dx < 0 else 0)
        oy = 0.15 if dy < 0 else (-0.15 if dy > 0 else 0.15)
        ax.text(points[0][0] + ox, points[0][1] + oy, card1,
                fontsize=7.5, fontweight='bold', color='#444444', ha='center', va='center')
    if card2:
        dx = points[-1][0] - points[-2][0]
        dy = points[-1][1] - points[-2][1]
        ox = 0.15 if dx < 0 else (-0.15 if dx > 0 else 0)
        oy = 0.15 if dy > 0 else (-0.15 if dy < 0 else 0.15)
        ax.text(points[-1][0] + ox, points[-1][1] + oy, card2,
                fontsize=7.5, fontweight='bold', color='#444444', ha='center', va='center')


# ===== TITLE =====
ax.text(9, 13.5, 'ER-диаграмма: структура базы данных ИАС',
        ha='center', va='center', fontsize=14, fontweight='bold', color='#333333')
ax.text(9, 13.1, 'Сущности и связи аналитической базы данных (PostgreSQL)',
        ha='center', va='center', fontsize=10, fontstyle='italic', color='#666666')

# ===== CREATE TABLES =====

# Row 1 (top): raw_reviews, batches, batch_summaries, alerts
t_reviews = Table(0.3, 12.5, 3.3, 'raw_reviews', [
    ('id', 'SERIAL'),
    ('text', 'TEXT'),
    ('rating', 'INT (1-5)'),
    ('order_id', 'VARCHAR'),
    ('review_date', 'TIMESTAMP'),
    ('source_type', "VARCHAR = 'oms'"),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'])

t_batches = Table(4.5, 12.5, 3.3, 'batches', [
    ('id', 'SERIAL'),
    ('source_type', 'VARCHAR'),
    ('batch_number', 'INT'),
    ('model_name', 'VARCHAR'),
    ('item_count', 'INT'),
    ('status', 'ENUM'),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'])

t_summaries = Table(8.7, 12.5, 3.5, 'batch_summaries', [
    ('id', 'SERIAL'),
    ('batch_id', 'INT'),
    ('summary_text', 'TEXT'),
    ('topics_agg', 'JSONB'),
    ('sentiment_dist', 'JSONB'),
    ('insights', 'JSONB'),
    ('raw_llm_response', 'TEXT'),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'], fk_fields=['batch_id'])

t_alerts = Table(13.2, 12.5, 3.3, 'alerts', [
    ('id', 'SERIAL'),
    ('report_id', 'INT'),
    ('alert_type', 'VARCHAR'),
    ('severity', 'ENUM'),
    ('message', 'TEXT'),
    ('is_acknowledged', 'BOOLEAN'),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'], fk_fields=['report_id'])

# Row 2 (bottom): raw_messages, analysis_items, reports, models_config
t_messages = Table(0.3, 6.5, 3.3, 'raw_messages', [
    ('id', 'SERIAL'),
    ('text', 'TEXT'),
    ('chat_id', 'BIGINT'),
    ('sender_name', 'VARCHAR'),
    ('message_date', 'TIMESTAMP'),
    ('source_type', "VARCHAR = 'tg'"),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'])

t_items = Table(4.5, 6.5, 3.8, 'analysis_items', [
    ('id', 'SERIAL'),
    ('source_id', 'INT'),
    ('source_type', 'VARCHAR'),
    ('batch_id', 'INT'),
    ('sentiment', 'ENUM(pos/neg/neu)'),
    ('sentiment_score', 'FLOAT'),
    ('topics', 'JSONB'),
    ('key_phrases', 'JSONB'),
    ('model_name', 'VARCHAR'),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'], fk_fields=['batch_id', 'source_id'])

t_reports = Table(9.3, 6.5, 3.5, 'reports', [
    ('id', 'SERIAL'),
    ('period_start', 'DATE'),
    ('period_end', 'DATE'),
    ('source_type', 'VARCHAR'),
    ('summary', 'TEXT'),
    ('top_problems', 'JSONB'),
    ('recommendations', 'JSONB'),
    ('model_name', 'VARCHAR'),
    ('created_at', 'TIMESTAMP'),
], pk_fields=['id'])

t_models = Table(13.8, 6.5, 3.5, 'models_config', [
    ('id', 'SERIAL'),
    ('model_name', 'VARCHAR'),
    ('provider', 'VARCHAR'),
    ('context_window', 'INT'),
    ('endpoint_url', 'VARCHAR'),
    ('is_active', 'BOOLEAN'),
], pk_fields=['id'])

# Draw all tables
for t in [t_reviews, t_batches, t_summaries, t_alerts,
          t_messages, t_items, t_reports, t_models]:
    t.draw()

# ===== RELATIONSHIPS (touching block edges) =====

# 1. raw_reviews (right) -> analysis_items (left) at source_id level
ry1 = t_reviews.field_y('id')
# Go from right edge of reviews, down, then to left edge of items
iy1 = t_items.field_y('source_id')
mid_x1 = 3.9
draw_rel([
    (t_reviews.right, ry1),
    (mid_x1, ry1),
    (mid_x1, iy1),
    (t_items.x, iy1),
], card1='1', card2='N')

# 2. raw_messages (right) -> analysis_items (left) at source_id
my1 = t_messages.field_y('id')
iy2 = t_items.field_y('source_type')
mid_x2 = 4.1
draw_rel([
    (t_messages.right, my1),
    (mid_x2, my1),
    (mid_x2, iy2),
    (t_items.x, iy2),
], card1='1', card2='N')

# 3. batches (bottom) -> analysis_items (top) at batch_id
bx3 = t_batches.cx - 0.3
draw_rel([
    t_batches.bottom_at(bx3),
    (bx3, t_batches.bottom - 0.3),
    (bx3, t_items.y + 0.3),
    t_items.top_at(bx3),
], card1='1', card2='N')

# 4. batches (right) -> batch_summaries (left) at batch_id
by4 = t_batches.field_y('id')
sy4 = t_summaries.field_y('batch_id')
draw_rel([
    (t_batches.right, by4),
    (t_summaries.x, sy4),
], card1='1', card2='1')

# 5. batch_summaries (bottom) -> reports (top)
sx5 = t_summaries.cx
draw_rel([
    t_summaries.bottom_at(sx5),
    (sx5, t_summaries.bottom - 0.4),
    (t_reports.cx, t_summaries.bottom - 0.4),
    (t_reports.cx, t_reports.y + 0.3),
    t_reports.top_at(t_reports.cx),
], card1='N', card2='1')

# 6. reports (right) -> alerts (bottom, coming down then right then up)
rr6 = t_reports.field_y('id')
al6 = t_alerts.field_y('report_id')
# Go right from reports, then up, then right to alerts bottom
mid_x6 = 13.0
draw_rel([
    (t_reports.right, rr6),
    (mid_x6, rr6),
    (mid_x6, al6),
    (t_alerts.x, al6),
], card1='1', card2='N')

# 7. models_config (left) -> batches: model_name reference
# Go from left edge of models_config up to bottom of batches
mx7 = t_models.cx - 0.5
bx7 = t_batches.cx + 0.5
my7 = t_models.field_y('model_name')
draw_rel([
    (t_models.x, my7),
    (t_models.x - 0.3, my7),
    (t_models.x - 0.3, t_batches.bottom - 0.5),
    (bx7, t_batches.bottom - 0.5),
    (bx7, t_batches.bottom),
], card1='1', card2='N')

# ===== LEGEND =====
ly = 0.7
ax.text(1, ly, 'Легенда:', fontsize=8, fontweight='bold', color='#333333')

ax.text(2.5, ly, 'PK', fontsize=8, fontweight='bold', color=PK_COLOR)
ax.text(3.2, ly, '= Primary Key', fontsize=8, color='#555555')

ax.text(5.5, ly, 'FK', fontsize=8, fontweight='bold', color=FK_COLOR)
ax.text(6.2, ly, '= Foreign Key', fontsize=8, color='#555555')

ax.text(8.5, ly, 'JSONB', fontsize=8, fontstyle='italic', color='#888888')
ax.text(9.8, ly, '= полуструктурированные данные', fontsize=8, color='#555555')

ax.plot(13.5, ly, 'o', color=REL_COLOR, markersize=3)
ax.plot([13.5, 14.2], [ly, ly], color=REL_COLOR, linewidth=1.3)
ax.plot(14.2, ly, 'o', color=REL_COLOR, markersize=3)
ax.text(14.5, ly, '= связь между таблицами', fontsize=8, color='#555555')

plt.tight_layout()
output = r'C:\Users\gudin\Downloads\Fig9_ER_Diagram.png'
plt.savefig(output, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {output}')
plt.close()
