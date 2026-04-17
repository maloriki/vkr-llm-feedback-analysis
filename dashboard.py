"""
ИАС Анализа Обратной Связи — Аналитический Дашборд
Streamlit dashboard для визуализации результатов LLM-анализа.
Запуск: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="ИАС Анализа Обратной Связи",
    page_icon="📊",
    layout="wide"
)

# ===== LOAD DATA =====
@st.cache_data
def load_data():
    data = {}

    # Load results JSONs
    for f in os.listdir('.'):
        if f.startswith('results_') and f.endswith('.json'):
            with open(f, 'r', encoding='utf-8') as fh:
                data[f] = json.load(fh)

    # Load predictions
    preds = {}
    if os.path.exists('predictions_qwen2.5_7b.csv'):
        preds['qwen'] = pd.read_csv('predictions_qwen2.5_7b.csv')
    if os.path.exists('predictions_tfidf_xgboost.csv'):
        preds['tfidf'] = pd.read_csv('predictions_tfidf_xgboost.csv')

    # Load test set
    test_df = None
    if os.path.exists('test_set_500.csv'):
        test_df = pd.read_csv('test_set_500.csv')

    return data, preds, test_df


data, preds, test_df = load_data()

# ===== HEADER =====
st.title("📊 ИАС Анализа Обратной Связи")
st.markdown("**Информационно-аналитическая система на основе LLM** | Дашборд сравнительного эксперимента")
st.divider()

# ===== SIDEBAR =====
with st.sidebar:
    st.header("⚙️ Фильтры")
    st.markdown("---")

    # Model selector
    available_models = []
    model_names = {}
    for f, d in data.items():
        m = d.get('model', f)
        available_models.append(m)
        model_names[m] = d

    selected_models = st.multiselect(
        "Модели для сравнения",
        available_models,
        default=available_models
    )

    st.markdown("---")
    st.markdown("**Датасет:** RuReviews")
    st.markdown("**Тест:** 500 отзывов")
    st.markdown("**Классы:** 3 (pos/neg/neu)")
    st.markdown("---")
    st.markdown("*ВКР Биксалин А. | НИУ ВШЭ 2026*")

# ===== TAB LAYOUT =====
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Сравнение моделей",
    "🔍 Анализ предсказаний",
    "💡 Инсайты LLM",
    "📋 Данные"
])

# ===== TAB 1: Model Comparison =====
with tab1:
    st.header("Сравнение моделей")

    # KPI cards
    cols = st.columns(len(selected_models))
    for i, model in enumerate(selected_models):
        d = model_names.get(model, {})
        with cols[i]:
            short_name = model.split('/')[-1][:15]
            st.metric(
                label=short_name,
                value=f"F1: {d.get('macro_f1', 0):.3f}",
                delta=f"Acc: {d.get('accuracy', 0):.3f}"
            )

    st.markdown("---")

    # Bar chart: Macro metrics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Общие метрики")
        metrics_df = pd.DataFrame([
            {
                'Модель': m,
                'Accuracy': model_names[m].get('accuracy', 0),
                'Macro F1': model_names[m].get('macro_f1', 0),
                'Macro Precision': model_names[m].get('macro_precision', 0),
                'Macro Recall': model_names[m].get('macro_recall', 0),
            }
            for m in selected_models
        ])

        fig = px.bar(
            metrics_df.melt(id_vars='Модель', var_name='Метрика', value_name='Значение'),
            x='Метрика', y='Значение', color='Модель',
            barmode='group',
            color_discrete_sequence=px.colors.qualitative.Set2,
            title='Accuracy, F1, Precision, Recall'
        )
        fig.update_layout(yaxis_range=[0, 1], height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("F1 по классам")
        per_class_rows = []
        for m in selected_models:
            pc = model_names[m].get('per_class', {})
            for cls in ['negative', 'neutral', 'positive']:
                if cls in pc:
                    per_class_rows.append({
                        'Модель': m,
                        'Класс': cls,
                        'F1': pc[cls].get('f1', 0)
                    })

        if per_class_rows:
            pc_df = pd.DataFrame(per_class_rows)
            fig2 = px.bar(
                pc_df, x='Класс', y='F1', color='Модель',
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Set2,
                title='F1-score по классам тональности'
            )
            fig2.update_layout(yaxis_range=[0, 1], height=400)
            st.plotly_chart(fig2, use_container_width=True)

    # Radar chart
    st.subheader("Радарная диаграмма: профиль моделей")
    categories = ['Accuracy', 'Neg F1', 'Neu F1', 'Pos F1']

    fig_radar = go.Figure()
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']

    for i, m in enumerate(selected_models):
        d = model_names[m]
        pc = d.get('per_class', {})
        vals = [
            d.get('accuracy', 0),
            pc.get('negative', {}).get('f1', 0),
            pc.get('neutral', {}).get('f1', 0),
            pc.get('positive', {}).get('f1', 0),
        ]
        vals.append(vals[0])  # close the polygon

        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=categories + [categories[0]],
            fill='toself',
            name=m,
            line=dict(color=colors[i % len(colors)])
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True, height=450
    )
    st.plotly_chart(fig_radar, use_container_width=True)


# ===== TAB 2: Predictions Analysis =====
with tab2:
    st.header("Анализ предсказаний")

    if 'qwen' in preds:
        qwen_df = preds['qwen']

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Распределение тональности (Qwen 2.5)")
            if 'qwen2.5_7b_pred' in qwen_df.columns:
                pred_col = 'qwen2.5_7b_pred'
            else:
                pred_col = [c for c in qwen_df.columns if '_pred' in c][0]

            pred_counts = qwen_df[pred_col].value_counts()
            fig_pie = px.pie(
                values=pred_counts.values,
                names=pred_counts.index,
                title='Предсказания Qwen 2.5 7B',
                color_discrete_map={
                    'positive': '#2ecc71',
                    'negative': '#e74c3c',
                    'neutral': '#f39c12'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader("Реальное распределение")
            true_counts = qwen_df['sentiment'].value_counts()
            fig_pie2 = px.pie(
                values=true_counts.values,
                names=true_counts.index,
                title='Ground Truth',
                color_discrete_map={
                    'positive': '#2ecc71',
                    'negative': '#e74c3c',
                    'neutral': '#f39c12'
                }
            )
            st.plotly_chart(fig_pie2, use_container_width=True)

        # Confusion analysis
        st.subheader("Ошибки модели Qwen 2.5")
        errors_df = qwen_df[qwen_df['sentiment'] != qwen_df[pred_col]].copy()
        st.write(f"Всего ошибок: **{len(errors_df)}** из {len(qwen_df)} ({len(errors_df)/len(qwen_df)*100:.1f}%)")

        # Filter errors
        error_type = st.selectbox(
            "Тип ошибки",
            ["Все", "negative → positive", "positive → negative",
             "neutral → negative", "neutral → positive",
             "negative → neutral", "positive → neutral"]
        )

        if error_type != "Все":
            parts = error_type.split(" → ")
            errors_df = errors_df[
                (errors_df['sentiment'] == parts[0]) &
                (errors_df[pred_col] == parts[1])
            ]

        st.dataframe(
            errors_df[['review', 'sentiment', pred_col]].head(20).rename(
                columns={'sentiment': 'Истина', pred_col: 'Предсказание', 'review': 'Отзыв'}
            ),
            use_container_width=True
        )
    else:
        st.info("Файл predictions_qwen2.5_7b.csv не найден")


# ===== TAB 3: LLM Insights =====
with tab3:
    st.header("💡 Инсайты LLM (Qwen 2.5)")

    if 'qwen' in preds:
        qwen_df = preds['qwen']

        topic_col = [c for c in qwen_df.columns if '_topic' in c]
        reason_col = [c for c in qwen_df.columns if '_reason' in c]

        if topic_col and reason_col:
            topic_col = topic_col[0]
            reason_col = reason_col[0]

            # Topic frequency
            st.subheader("Топ-15 тем в отзывах")
            topics = qwen_df[topic_col].dropna()
            topics = topics[topics.str.len() > 0]
            topic_counts = topics.value_counts().head(15)

            fig_topics = px.bar(
                x=topic_counts.values,
                y=topic_counts.index,
                orientation='h',
                title='Частота тем (выделены LLM)',
                labels={'x': 'Количество', 'y': 'Тема'},
                color=topic_counts.values,
                color_continuous_scale='RdYlGn_r'
            )
            fig_topics.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig_topics, use_container_width=True)

            # Filter by sentiment
            st.subheader("Инсайты по тональности")
            pred_col = [c for c in qwen_df.columns if '_pred' in c][0]
            sentiment_filter = st.selectbox(
                "Фильтр по тональности",
                ["Все", "negative", "neutral", "positive"]
            )

            display_df = qwen_df.copy()
            if sentiment_filter != "Все":
                display_df = display_df[display_df[pred_col] == sentiment_filter]

            st.dataframe(
                display_df[['review', pred_col, topic_col, reason_col]]
                .rename(columns={
                    'review': 'Отзыв',
                    pred_col: 'Тональность',
                    topic_col: 'Тема',
                    reason_col: 'Причина (инсайт)'
                })
                .head(50),
                use_container_width=True,
                height=500
            )

            # Key insight
            st.subheader("🚨 Ключевой инсайт")
            neg_topics = qwen_df[qwen_df[pred_col] == 'negative'][topic_col].dropna()
            if len(neg_topics) > 0:
                top_neg = neg_topics.value_counts().head(3)
                st.error(
                    f"**Топ причины негативных отзывов:** "
                    f"{', '.join([f'{t} ({c} шт.)' for t, c in top_neg.items()])}"
                )
        else:
            st.info("Данные инсайтов не найдены")
    else:
        st.info("Файл predictions_qwen2.5_7b.csv не найден")


# ===== TAB 4: Raw Data =====
with tab4:
    st.header("Данные эксперимента")

    st.subheader("Результаты моделей (JSON)")
    for m in selected_models:
        with st.expander(f"📄 {m}"):
            st.json(model_names[m])

    if test_df is not None:
        st.subheader("Тестовая выборка")
        st.write(f"Размер: {len(test_df)} отзывов")
        st.dataframe(test_df.head(20), use_container_width=True)

    # Analytical report demo
    if os.path.exists('analytical_report_demo.md'):
        st.subheader("Пример аналитического отчёта (MAP-фаза)")
        with open('analytical_report_demo.md', 'r', encoding='utf-8') as f:
            report = f.read()
        st.markdown(report)
