import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import io
import os

# --- САҲИФА СОЗЛАМАЛАРИ ---
st.set_page_config(page_title="AI Monitoring Platform", layout="wide")

# --- ШРИФТ СОЗЛАМАЛАРИ ---
# Онлайн (GitHub/Streamlit Cloud) учун шрифт йўли
font_path = "arial.ttf" 

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('ArialCustom', font_path))
    FONT_NAME = 'ArialCustom'
else:
    # Агар шрифт топилмаса стандартга қайтади
    FONT_NAME = 'Helvetica'

# --- МАЪЛУМОТЛАР БАЗАСИ ---
def init_db():
    conn = sqlite3.connect('university_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, faculty TEXT, 
                  dept_group TEXT, fio TEXT, position TEXT, cert_name TEXT, cert_data BLOB)''')
    
    # cert_data устунини текшириш (агар эски база бўлса)
    try:
        c.execute("ALTER TABLE data ADD COLUMN cert_data BLOB")
    except sqlite3.OperationalError:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS faculties (name TEXT UNIQUE)''')
    
    # "ИТ" олиб ташланган бошланғич рўйхат
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

# --- PDF ГЕНЕРАЦИЯ (3x4 РАСМ БИЛАН) ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Title']
    title_style.fontName = FONT_NAME
    elements.append(Paragraph(f"Ҳисобот: {title}", title_style))
    
    table_data = [["FIO", "Гуруҳ/Кафедра", "Факультет", "Сертификат (3x4)"]]
    
    for row in records:
        fio, group, faculty, img_blob = row
        if img_blob:
            img_io = io.BytesIO(img_blob)
            img = Image(img_io)
            img.drawWidth = 4 * cm 
            img.drawHeight = 3 * cm
            img_to_display = img
        else:
            img_to_display = "Йўқ"
        table_data.append([fio, group, faculty, img_to_display])
    
    t = Table(table_data, colWidths=[6*cm, 5*cm, 6*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

# --- АСОСИЙ ЛОГИКА ---
menu = st.sidebar.selectbox("Ролингизни танланг:", ["Бош саҳифа", "Талаба", "Ўқитувчи", "Administrator"])

if 'access' not in st.session_state:
    st.session_state.access = True

if menu == "Administrator":
    pwd = st.sidebar.text_input("Паролни киритинг:", type="password")
    if pwd == "Jo12100105+":
        st.header("🛠 Администратор панели")
        st.session_state.access = st.toggle("Тизимга киришни очиш/ёпиш", value=st.session_state.access)
        
        tab1, tab2, tab3 = st.tabs(["📊 Графиклар", "📋 PDF Ҳисобот", "⚙ Созламалар"])
        
        with tab1:
            data_df = pd.read_sql("SELECT role, faculty, dept_group FROM data", conn)
            if not data_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Ўқитувчилар")
                    t_data = data_df[data_df['role'] == 'Ўқитувчи']['faculty'].value_counts()
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
            role_f = st.radio("Кимлар бўйича:", ["Ўқитувчи", "Талаба"], horizontal=True)
            c.execute(f"SELECT fio, dept_group, faculty, cert_data FROM data WHERE role='{role_f}'")
            recs = c.fetchall()
            if recs:
                if st.button(f"{role_f}лар ҳисоботини PDF юклаш"):
                    pdf_bytes = generate_pdf(recs, role_f)
                    st.download_button("Файлни сақлаш", pdf_bytes, f"hisobot_{role_f}.pdf", "application/pdf")
                df_v = pd.DataFrame(recs, columns=["FIO", "Гуруҳ", "Факультет", "Blob"]).drop(columns=["Blob"])
                st.dataframe(df_v, use_container_width=True)
            else:
                st.info("Маълумот мавжуд эмас.")

        with tab3:
            st.subheader("Факультетларни бошқариш")
            # Факультет қўшиш
            new_f = st.text_input("Янги факультет номи:")
            if st.button("Қўшиш"):
                if new_f:
                    c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                    conn.commit()
                    st.success("Қўшилди!")
                    st.rerun()
            
            st.divider()
            
            # Факультетни ўчириш
            facs_list = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
            delete_fac = st.selectbox("Ўчириш учун факультетни танланг:", facs_list)
            if st.button("Танланган факультетни ўчириш"):
                c.execute("DELETE FROM faculties WHERE name = ?", (delete_fac,))
                conn.commit()
                st.warning(f"{delete_fac} ўчирилди!")
                st.rerun()

    else:
        st.warning("Админ паролини киритинг.")

elif menu in ["Талаба", "Ўқитувчи"]:
    if st.session_state.access:
        st.header(f"{menu} анкетаси")
        facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
        with st.form("user_form"):
            f_fio = st.text_input("Ф.И.О:")
            f_fac = st.selectbox("Факультет:", facs)
            f_group = st.text_input("Гуруҳ / Кафедра:")
            f_file = st.file_uploader("Сертификат расми", type=['jpg','png','jpeg'])
            if st.form_submit_button("Сақлаш"):
                if f_fio and f_file:
                    binary_img = f_file.read()
                    c.execute("INSERT INTO data (role, faculty, dept_group, fio, position, cert_name, cert_data) VALUES (?,?,?,?,?,?,?)",
                              (menu, f_fac, f_group, f_fio, "", f_file.name, binary_img))
                    conn.commit()
                    st.success("Маълумотларингиз базага қўшилди!")
                else:
                    st.error("Ф.И.О ва расм мажбурий!")
    else:
        st.error("Тизим вақтинча ёпиқ.")

else:
    st.title("Университет СИ курси мониторинги")
    st.info("Чап менюдан керакли бўлимни танланг.")
