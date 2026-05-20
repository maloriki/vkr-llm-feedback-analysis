# Диаграммы ВКР

Все 12 рисунков из текста ВКР с актуальными финальными версиями.

## Структура

- **images/** — финальные PNG, в точности как в [VKR_Biksalin_final.pdf](../vkr_thesis/VKR_Biksalin_final.pdf)
- **sources/** — редактируемые исходники: `.drawio` (draw.io / diagrams.net), `.bpmn` (Camunda Modeler / bpmn.io), `.puml` (PlantUML), `.archimate` (Archi)
- **svg/** — векторные версии (масштабируются без потери качества)
- **code/** — python-генераторы (для воспроизводимости диаграмм из matplotlib)

## Соответствие диаграмм разделам ВКР

| № | Файл (PNG) | Источник | Глава ВКР | Содержание |
|---|---|---|---|---|
| 1 | Fig1_ArchiMate_BizCoop_ASIS | `.drawio` + `.svg` | 1.4 | ArchiMate Business Cooperation AS-IS — модель организации |
| 2 | Fig2_BPMN_ASIS | `.svg` (из draw.io) | 1.4 | BPMN 2.0 — текущий процесс ручного анализа |
| 3 | Fig3_Ishikawa | `.drawio` + `.svg` | 1.4 | Диаграмма Исикавы — 5 категорий корневых причин |
| 4 | Fig4_ArchiMate_BizCoop_TOBE | `.drawio` + `.svg` | 2.3 | ArchiMate Business Cooperation TO-BE — модель после внедрения |
| 5 | Fig5_C4_Context | `.drawio` | 2.2 | C4 Context Diagram — система в окружении |
| 6 | Fig6_C4_Container | `.drawio` | 2.2 | C4 Container Diagram — 9 контейнеров |
| 7 | Fig7_C4_Component_LLM_Pipeline | `.drawio` | 2.2 | C4 Component Diagram — внутренняя структура LLM Pipeline |
| 8 | Fig8_BPMN_TOBE | `.drawio` + `.bpmn` + `.svg` | 2.3 | BPMN TO-BE — целевой процесс с ИАС |
| 9 | Fig9_UML_Activity | `.puml` | 2.4 | UML Activity Diagram — конвейер MapReduce |
| 10 | Fig10_ER_Diagram | `.puml` | 2.5 | ER-диаграмма БД (8 таблиц) |
| 11 | Fig11_Risk_Matrix | `.drawio` | 2.7 | Матрица рисков (12 рисков, probability × impact) |
| 12 | Fig12_Bootstrap_CI | — | 3.3 | F1-макро с 95% bootstrap-CI для 6 моделей |

## Дополнительные исходники

- `ArchiMate_BizCoop_Model.archimate` — мастер-файл Archi (содержит обе модели AS-IS и TO-BE)
- `ArchiMate_BizCoop_Model.xml` — XML-экспорт ArchiMate-модели

## Как открыть/редактировать

| Формат | Чем открыть |
|---|---|
| `.drawio` | https://app.diagrams.net (онлайн) или Draw.io Desktop |
| `.bpmn` | https://bpmn.io/demo, Camunda Modeler |
| `.puml` | https://www.plantuml.com/plantuml/uml/ |
| `.archimate` | https://www.archimatetool.com (Archi) |
| `.svg` | любой браузер, Inkscape, Adobe Illustrator |

## Воспроизводимость

В папке `code/` лежат python-генераторы для тех диаграмм, которые изначально создавались скриптами на matplotlib. Запуск:

```bash
pip install matplotlib
python code/diagram_ishikawa.py
python code/diagram_risk_matrix.py
# ...
```
