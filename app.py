import streamlit as st
import pandas as pd
from io import BytesIO
import base64

# Настройки приложения
st.set_page_config(
    page_title="График смен",
    layout="wide",
    page_icon="📅"
)

# Стили для адаптивности
st.markdown("""
<style>
@media (max-width: 768px) {
    /* Мобильные стили */
    .stTextInput input, .stSelectbox select {
        font-size: 14px !important;
    }
    .stButton button {
        width: 100% !important;
    }
    .stDataFrame {
        font-size: 12px !important;
    }
    .stTabs [role=tablist] button {
        padding: 0.25rem 0.5rem !important;
        font-size: 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Функция для создания PWA манифеста
def create_pwa_manifest():
    manifest = {
        "name": "Генератор графика смен",
        "short_name": "График смен",
        "description": "Приложение для создания графиков смен сотрудников",
        "start_url": ".",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#4f8bf9",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3652/3652191.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    }
    return manifest

# Основной интерфейс
st.title("📅 Генератор графика смен по пожеланиям сотрудников")

tab1, tab2 = st.tabs(["📤 Загрузить Excel", "📝 Ввести вручную"])

# --------- Таб "Загрузить Excel" ----------
with tab1:
    st.markdown("""
    **Загрузите Excel-файл с пожеланиями сотрудников.**

    Требуемый формат:
    - Столбец `Сотрудник` (имена сотрудников)
    - Столбцы с днями недели: `Пн`, `Вт`, `Ср`, `Чт`, `Пт`, `Сб`, `Вс`
    - Допустимые значения в ячейках: 
        - `7-15` (утренняя смена)
        - `15-23` (вечерняя смена)
        - `выходной`
    """)

    uploaded_file = st.file_uploader("Выберите файл Excel", type=["xlsx"], key="file_uploader")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ['Сотрудник'] + ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            
            if all(col in df.columns for col in required_columns):
                st.success("Файл успешно загружен и проверен!")
                st.write("Предпросмотр данных:")
                st.dataframe(df.head())
            else:
                st.error("Ошибка: В файле отсутствуют необходимые столбцы. Пожалуйста, проверьте формат.")
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {e}")

# --------- Таб "Ввести вручную" ----------
with tab2:
    st.markdown("**Заполните данные о сотрудниках и их пожеланиях**")

    num_people = st.number_input(
        "Количество сотрудников", 
        min_value=1, 
        max_value=50, 
        value=1,
        help="Укажите количество сотрудников для добавления в график"
    )

    data = []
    for i in range(num_people):
        with st.expander(f"Сотрудник {i+1}", expanded=True if i == 0 else False):
            name = st.text_input(f"ФИО сотрудника", key=f"name_{i}")
            
            cols = st.columns(7)
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            day_data = {}
            
            for j, day in enumerate(days):
                with cols[j]:
                    day_data[day] = st.selectbox(
                        day,
                        options=["", "7-15", "15-23", "выходной"],
                        key=f"{day}_{i}"
                    )
            
            if name:
                row = {"Сотрудник": name, **day_data}
                data.append(row)

    if st.button("Сформировать график", key="generate_btn"):
        if data:
            df = pd.DataFrame(data)
            st.success("Данные успешно сохранены!")
        else:
            st.warning("Добавьте хотя бы одного сотрудника")

# --------- Генерация расписания (общая часть) ----------
if 'df' in locals() and not df.empty:
    st.subheader("📊 Итоговый график смен")
    
    # Преобразование данных
    schedule = []
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    for day in days:
        morning_shift = df[df[day] == "7-15"]['Сотрудник'].tolist()
        evening_shift = df[df[day] == "15-23"]['Сотрудник'].tolist()
        
        schedule.append({
            "День недели": day,
            "Утренняя смена (7-15)": ", ".join(morning_shift) if morning_shift else "—",
            "Вечерняя смена (15-23)": ", ".join(evening_shift) if evening_shift else "—"
        })
    
    schedule_df = pd.DataFrame(schedule)
    st.dataframe(schedule_df, use_container_width=True)
    
    # Экспорт в Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        schedule_df.to_excel(writer, index=False, sheet_name='График смен')
    
    st.download_button(
        label="Скачать график (Excel)",
        data=output.getvalue(),
        file_name="график_смен.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# PWA установка
st.markdown("""
<script>
// Проверяем, поддерживает ли браузер PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker registration successful');
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Показываем кнопку "Установить" когда это возможно
let deferredPrompt;
const addBtn = document.createElement('button');
addBtn.style.display = 'none';
document.body.appendChild(addBtn);

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    addBtn.style.display = 'block';
    
    addBtn.addEventListener('click', () => {
        addBtn.style.display = 'none';
        deferredPrompt.prompt();
        
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
        });
    });
});
</script>
""", unsafe_allow_html=True)

# Кнопка установки PWA
st.button("Установить приложение", key="install_btn", help="Добавить это приложение на главный экран вашего устройства")
