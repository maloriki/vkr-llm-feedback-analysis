# 📊 Диаграммы ВКР

В этой папке собраны все диаграммы из ВКР и Python-скрипты для их генерации.
Все диаграммы построены с помощью `matplotlib` без сторонних BPMN/UML-инструментов
— это даёт полный контроль над оформлением и воспроизводимость.

## Структура

```
diagrams/
├── README.md            ← этот файл
├── code/                ← Python-скрипты генерации
└── images/              ← готовые PNG (200 DPI)
```

## Перегенерация диаграмм

```bash
pip install matplotlib
cd diagrams/code
python diagram_org_view_ru.py   # → ../images/Fig1_Organization_View.png
python diagram_bpmn_asis.py     # → ../images/Fig2_BPMN_ASIS.png
# ... и так далее
```

**Примечание:** пути сохранения внутри скриптов настроены на
`C:\Users\gudin\Downloads\`. На новой машине нужно поправить переменную `output`
в конце каждого скрипта на актуальный путь.

## Список диаграмм

| № | Файл изображения | Скрипт | Нотация | Содержание |
|---|---|---|---|---|
| 1 | `Fig1_Organization_View.png` | `diagram_org_view_ru.py` | **ArchiMate** Organization View | Организационная модель AS-IS: 4 подразделения работают с обратной связью изолированно, нет единой аналитической платформы |
| 2 | `Fig2_BPMN_ASIS.png` | `diagram_bpmn_asis.py` | **BPMN 2.0** (waterfall) | Текущий процесс: 5 swim-lanes (DWH → Оп. аналитик → Дашборд → Менеджер → Руководитель), узкое место — поиск по ключевым словам |
| 3 | `Fig3_Ishikawa.png` | `diagram_ishikawa.py` | **Диаграмма Исикавы** | Корневые причины неэффективности по 5 категориям: персонал, процесс, технологии, данные, время |
| 4 | `Fig4_ArchiMate_App.png` | `diagram_archimate_app.py` | **ArchiMate** Application Cooperation | TO-BE: программные компоненты системы (OMS Connector, Telegram Bot, LLM Pipeline, Dashboard) и потоки данных между ними |
| 5 | `Fig5_BPMN_TOBE.png` | `diagram_bpmn_tobe.py` | **BPMN 2.0** (waterfall) | Целевой процесс с ИАС: параллельный сбор данных, LLM-конвейер (Map/Reduce), автоматические алерты |
| 6 | `Fig6_C4_Context.png` | `diagram_c4_context.py` | **C4** Context Diagram | Система в окружении: 4 группы пользователей, 3 внешние системы (OMS, Telegram, Email) |
| 7 | `Fig7_C4_Container.png` | `diagram_c4_container.py` | **C4** Container Diagram | 9 контейнеров внутри ИАС: коннекторы, хранилища, LLM-сервер, дашборд, API, уведомления |
| 8 | `Fig8_UML_Activity.png` | `diagram_uml_activity.py` | **UML** Activity Diagram | Детальная логика LLM-конвейера: 5 фаз (подготовка, batching, Map, Reduce, доставка) |
| 9 | `Fig9_ER_Diagram.png` | `diagram_er.py` | **ER-диаграмма** | Структура БД: 8 таблиц с FK-связями (raw_reviews, raw_messages, batches, analysis_items, batch_summaries, reports, alerts, models_config) |
| 10 | `Fig11_Risk_Matrix.png` | `diagram_risk_matrix.py` | **Heatmap** | Матрица 12 рисков проекта по осям «вероятность × влияние» с цветовой подсветкой (зелёный/жёлтый/оранжевый/красный) |

## Бонус: неиспользованные диаграммы

| Файл | Статус | Комментарий |
|---|---|---|
| `Fig10_Gantt.png` | **Удалена из ВКР** | Диаграмма Ганта с планом внедрения на 12 месяцев. Убрана с защиты, так как при отсутствии реального опыта project-менеджмента создавала уязвимость на защите (вопросы «как вы обосновали сроки?»). Код оставлен в репозитории — может пригодиться. |
| `diagram_gantt.py` | Код доступен | См. выше |

## Маппинг «рисунок в ВКР → файл»

В тексте ВКР рисунки нумеруются 1-10 (без Ганта, который удалён).
Рисунок 10 в тексте соответствует `Fig11_Risk_Matrix.png` — это исторический
остаток от того, что Гант был Fig10, а матрицу рисков добавили под номером 11.

| Номер в ВКР | Файл |
|---|---|
| Рисунок 1 | `Fig1_Organization_View.png` |
| Рисунок 2 | `Fig2_BPMN_ASIS.png` |
| Рисунок 3 | `Fig3_Ishikawa.png` |
| Рисунок 4 | `Fig4_ArchiMate_App.png` |
| Рисунок 5 | `Fig6_C4_Context.png` |
| Рисунок 6 | `Fig7_C4_Container.png` |
| Рисунок 7 | `Fig5_BPMN_TOBE.png` |
| Рисунок 8 | `Fig8_UML_Activity.png` |
| Рисунок 9 | `Fig9_ER_Diagram.png` |
| Рисунок 10 | `Fig11_Risk_Matrix.png` |

## Технические детали

- **Размер изображений:** 200 DPI, PNG с белым фоном
- **Шрифт:** Arial / DejaVu Sans (для кириллицы)
- **Цветовая палитра:** ArchiMate-стандартная (синий, зелёный, фиолетовый,
  жёлтый, оранжевый)
- **Соглашения BPMN:** waterfall-стиль (поток сверху вниз через
  горизонтальные дорожки) — выбран автором как более наглядный для
  отображения каскада ответственности

## Зависимости

```bash
pip install matplotlib
```

Никаких сторонних BPMN/ArchiMate/UML-инструментов не требуется. Всё рисуется
через `matplotlib.patches.FancyBboxPatch`, `Circle`, `Polygon` и аннотации.
