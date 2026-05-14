import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import io
import os

# --- САҲИФА СОЗЛАМАЛАРИ ---
st.set_page_config(page_title="AI Monitoring Platform", layout="wide")

# --- ШРИФТ СОЗЛАМАЛАРИ ---
font_path = "arial.ttf" 
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('ArialCustom', font_path))
    FONT_NAME = 'ArialCustom'
else:
    FONT_NAME = 'Helvetica'

# --- МАЪЛУМОТЛАР БАЗАСИНИ ЯНГИЛАШ ---
def init_db():
    conn = sqlite3.connect('university_ai.db', check_same_thread=False)
    c = conn.cursor()
    # Асосий жадвални яратиш
    c.execute('''CREATE TABLE IF NOT EXISTS data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, faculty TEXT, 
                  dept_group TEXT, fio TEXT, cert_link TEXT)''')
    
    # ЭСКИ БАЗАНИ АВТОМАТИК ЯНГИЛАШ (Хатоликни олдини олиш учун)
    try:
        # cert_link устуни борлигини текшириб кўрамиз
        c.execute("SELECT cert_link FROM data LIMIT 1")
    except sqlite3.OperationalError:
        # Агар устун бўлмаса (эски база бўлса), уни қўшамиз
        try:
            c.execute("ALTER TABLE data ADD COLUMN cert_link TEXT")
            conn.commit()
        except:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS faculties (name TEXT UNIQUE)''')
    
    # Факультетлар рўйхати (ИТ олиб ташланган)
    default_facs = ["Энергетика", "Машинасозлик", "Иқтисодиёт", "Қурилиш", "Транспорт", "Биотехнология", "Енгил саноат", "Табиий фанлар"]
    for f in default_facs:
        c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (f,))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ДИЗАЙН ВА ФУТЕР ---
st.markdown("""
    <style>
    .footer { 
        position: fixed; right: 20px; bottom: 20px; color: #888; 
        font-weight: bold; z-index: 1000; background: rgba(255,255,255,0.8); 
        padding: 5px 15px; border-radius: 8px; border: 1px solid #ddd;
    }
    </style>
    <div class="footer">Created by Jakbarov Odiljon</div>
    """, unsafe_allow_html=True)

# --- PDF ГЕНЕРАЦИЯ ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Title']
    title_style.fontName = FONT_NAME
    elements.append(Paragraph(f"Ҳисобот: {title}", title_style))
    
    table_data = [["FIO", "Гуруҳ/Кафедра", "Факультет", "Сертификат ҳаволаси"]]
    
    for row in records:
        # Фақат керакли устунларни оламиз
        fio, group, faculty, link = row
        table_data.append([fio, group, faculty, link if link else "Йўқ"])
    
    t = Table(table_data, colWidths=[6*cm, 5*cm, 6*cm, 8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

# --- МЕНЮ ---
menu = st.sidebar.selectbox("Бўлимни танланг:", ["Бош саҳифа", "Талаба", "Ўқитувчи ва ходим", "Administrator"])

if 'access' not in st.session_state:
    st.session_state.access = True

if menu == "Administrator":
    pwd = st.sidebar.text_input("Парол:", type="password")
    if pwd == "Jo12100105+":
        st.header("🛠 Администратор панели")
        st.session_state.access = st.toggle("Рўйхатга олишни ёпиш/очиш", value=st.session_state.access)
        
        tab1, tab2, tab3 = st.tabs(["📊 Статистика", "📋 Ҳисобот (PDF)", "⚙ Созламалар"])
        
        with tab1:
            data_df = pd.read_sql("SELECT role, faculty, dept_group FROM data", conn)
            if not data_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Ходимлар")
                    t_data = data_df[data_df['role'] == 'Ўқитувчи ва ходим']['faculty'].value_counts()
                    if not t_data.empty:
                        fig, ax = plt.subplots()
                        t_data.plot(kind='bar', color='#1E3A8A', ax=ax)
                        st.pyplot(fig)
                with col2:
                    st.subheader("Талабалар")
                    s_data = data_df[data_df['role'] == 'Талаба']['dept_group'].value_counts()
                    if not s_data.empty:
                        fig2, ax2 = plt.subplots()
                        s_data.plot(kind='bar', color='#10B981', ax=ax2)
                        st.pyplot(fig2)
        
        with tab2:
            role_f = st.radio("Кимлар бўйича:", ["Ўқитувчи ва ходим", "Талаба"], horizontal=True)
            c.execute(f"SELECT fio, dept_group, faculty, cert_link FROM data WHERE role='{role_f}'")
            recs = c.fetchall()
            if recs:
                if st.button("PDF файлни тайёрлаш"):
                    pdf_bytes = generate_pdf(recs, role_f)
                    st.download_button("Юклаб олиш", pdf_bytes, f"{role_f}_hisobot.pdf", "application/pdf")
                df_view = pd.DataFrame(recs, columns=["FIO", "Гуруҳ/Кафедра", "Факультет", "Ҳавола"])
                st.dataframe(df_view, use_container_width=True)
            else:
                st.info("Маълумот йўқ.")

        with tab3:
            st.subheader("Факультетлар")
            new_f = st.text_input("Янги факультет номи:")
            if st.button("Қўшиш"):
                if new_f:
                    c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                    conn.commit()
                    st.success("Қўшилди!")
                    st.rerun()
            
            facs_list = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
            del_fac = st.selectbox("Ўчириш:", facs_list)
            if st.button("Ўчириш"):
                c.execute("DELETE FROM faculties WHERE name = ?", (del_fac,))
                conn.commit()
                st.warning(f"{del_fac} олиб ташланди.")
                st.rerun()
    else:
        st.warning("Парол киритилмаган.")

elif menu in ["Талаба", "Ўқитувчи ва ходим"]:
    if st.session_state.access:
        st.header(f"{menu} учун анкета")
        facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
        with st.form("main_form"):
            f_fio = st.text_input("Ф.И.О (Тўлиқ):")
            f_fac = st.selectbox("Факультет:", facs)
            f_group = st.text_input("Гуруҳ ёки Кафедра:")
            f_link = st.text_input("Сертификат ҳаволаси (Link):")
            
            if st.form_submit_button("Сақлаш"):
                if f_fio and f_link:
                    c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)",
                              (menu, f_fac, f_group, f_fio, f_link))
                    conn.commit()
                    st.success("Маълумот қабул қилинди!")
                else:
                    st.error("Маълумотларни тўлиқ киритинг!")
    else:
        st.error("Тизим ҳозирда ёпиқ.")
else:
    st.title("Университет СИ курси мониторинги")
    st.info("Давом этиш учун чап томондан ролни танланг.")
