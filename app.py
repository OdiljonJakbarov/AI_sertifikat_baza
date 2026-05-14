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
font_path = "font_path = arial.ttf" 
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
                  dept_group TEXT, fio TEXT, position TEXT, cert_name TEXT)''')
    
    # cert_data устуни бор-йўқлигини текшириш ва қўшиш
    try:
        c.execute("ALTER TABLE data ADD COLUMN cert_data BLOB")
    except sqlite3.OperationalError:
        pass # Устун аллақачон мавжуд бўлса
        
    c.execute('''CREATE TABLE IF NOT EXISTS faculties (name TEXT UNIQUE)''')
    
    default_facs = ["Муҳандислик ахборот технологиялари", "Энергетика", "Машинасозлик", "Иқтисодиёт", "Қурилиш", "Транспорт", "Биотехнология", "Енгил саноат", "Табиий фанлар"]
    for f in default_facs:
        c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (f,))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ДИЗАЙН ---
st.markdown("""
    <style>
    .footer { position: fixed; right: 20px; bottom: 20px; color: #888; font-weight: bold; z-index: 1000; background: rgba(255,255,255,0.8); padding: 5px; border-radius: 5px;}
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
    
    # Жадвал боши
    table_data = [["FIO", "Гуруҳ/Кафедра", "Факультет", "Сертификат (3x4)"]]
    
    for row in records:
        fio, group, faculty, img_blob = row
        
        if img_blob:
            img_io = io.BytesIO(img_blob)
            img = Image(img_io)
            # 3см x 4см ўлчамга мослаш (1см = 28.35 point)
            img.drawWidth = 4 * cm 
            img.drawHeight = 3 * cm
            img_to_display = img
        else:
            img_to_display = "Юкланмаган"
            
        table_data.append([fio, group, faculty, img_to_display])
    
    # Жадвал стили
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

# --- МЕНЮ ВА ЛОГИКА ---
menu = st.sidebar.selectbox("Рол:", ["Бош саҳифа", "Талаба", "Ўқитувчи", "Administrator"])

if menu == "Administrator":
    pwd = st.sidebar.text_input("Парол:", type="password")
    if pwd == "Jo12100105+":
        st.header("Администратор панели")
        role_filter = st.radio("Тури:", ["Ўқитувчи", "Талаба"], horizontal=True)
        
        c.execute(f"SELECT fio, dept_group, faculty, cert_data FROM data WHERE role='{role_filter}'")
        records = c.fetchall()
        
        if records:
            # Юклаш учун PDF
            if st.button("Ҳисоботни PDF қилиб юклаш (Расмлар билан)"):
                pdf_bytes = generate_pdf(records, role_filter)
                st.download_button("Файлни сақлаш", pdf_bytes, f"hisobot_{role_filter}.pdf", "application/pdf")
            
            # Экранда кўриш учун жадвал (расмсиз)
            df_view = pd.DataFrame(records, columns=["ФИО", "Гуруҳ/Кафедра", "Факультет", "Блоб"]).drop(columns=["Блоб"])
            st.dataframe(df_view, use_container_width=True)
        else:
            st.info("Ҳозирча маълумот йўқ.")

elif menu in ["Талаба", "Ўқитувчи"]:
    st.header(f"{menu} анкетаси")
    with st.form("my_form"):
        fio = st.text_input("Ф.И.О:")
        fac = st.selectbox("Факультет:", [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()])
        group = st.text_input("Гуруҳ / Кафедра:")
        file = st.file_uploader("Сертификат расмини юкланг", type=['jpg','png','jpeg'])
        
        if st.form_submit_button("Сақлаш"):
            if fio and file:
                img_binary = file.read()
                c.execute("INSERT INTO data (role, faculty, dept_group, fio, position, cert_name, cert_data) VALUES (?,?,?,?,?,?,?)",
                          (menu, fac, group, fio, "", file.name, img_binary))
                conn.commit()
                st.success("Маълумотлар сақланди!")
            else:
                st.error("Ф.И.О ва расм мажбурий!")

else:
    st.title("Университет СИ курси мониторинги")
    st.write("Чап менюдан ролингизни танланг.")
