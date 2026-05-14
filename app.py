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

# --- SAHIFA SOZLAMALARI ---
st.set_page_config(page_title="AI Monitoring Platform", layout="wide")

# --- SHRIFT SOZLAMALARI ---
font_path = "arial.ttf" 
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('ArialCustom', font_path))
    FONT_NAME = 'ArialCustom'
else:
    FONT_NAME = 'Helvetica'

# --- MA'LUMOTLAR BAZASINI INIZIALIZATSIYA QILISH ---
def init_db():
    conn = sqlite3.connect('university_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, faculty TEXT, 
                  dept_group TEXT, fio TEXT, cert_link TEXT)''')
    
    # Ustun borligini tekshirish
    c.execute("PRAGMA table_info(data)")
    cols = [column[1] for column in c.fetchall()]
    if 'cert_link' not in cols:
        try:
            c.execute("ALTER TABLE data ADD COLUMN cert_link TEXT")
            conn.commit()
        except: pass

    c.execute('''CREATE TABLE IF NOT EXISTS faculties (name TEXT UNIQUE)''')
    default_facs = ["Energetika", "Mashinasozlik", "Iqtisodiyot", "Qurilish", "Transport", "Biotexnologiya", "Yengil sanoat", "Tabiiy fanlar"]
    for f in default_facs:
        c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (f,))
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- DIZAYN VA FUTER ---
st.markdown("""
    <style>
    .footer { position: fixed; right: 20px; bottom: 20px; color: #888; font-weight: bold; z-index: 1000; }
    </style>
    <div class="footer">Created by Jakbarov Odiljon</div>
    """, unsafe_allow_html=True)

# --- PDF GENERATSIYA ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = FONT_NAME
    elements.append(Paragraph(f"Hisobot: {title}", title_style))
    
    table_data = [["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat"]]
    for row in records:
        table_data.append([str(x) if x else "Yo'q" for x in row])
    
    t = Table(table_data, colWidths=[6*cm, 5*cm, 6*cm, 8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

def generate_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Hisobot")
    return output.getvalue()

# --- ASOSIY QISM ---
menu = st.sidebar.selectbox("Bo'limni tanlang:", ["Bosh sahifa", "Talaba", "O'qituvchi va xodim", "Administrator"])

if menu == "Administrator":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "Jo12100105+":
        st.header("🛠 Administrator paneli")
        tab1, tab2, tab3 = st.tabs(["📊 Statistika", "📋 Hisobot yuklash", "⚙ Sozlamalar"])
        
        with tab2:
            role_f = st.radio("Kimlar bo'yicha:", ["O'qituvchi va xodim", "Talaba"], horizontal=True)
            
            # XAVFSIZ SELECT: Agar ustun bo'lmasa, xato bermaydi
            query = "SELECT fio, dept_group, faculty, cert_link FROM data WHERE role=?"
            try:
                c.execute(query, (role_f,))
                recs = c.fetchall()
            except sqlite3.OperationalError:
                # Agar cert_link bo'lmasa, uni bo'sh holda olamiz
                c.execute("SELECT fio, dept_group, faculty, 'Yo''q' as cert_link FROM data WHERE role=?", (role_f,))
                recs = c.fetchall()
            
            if recs:
                df_view = pd.DataFrame(recs, columns=["F.I.O", "Guruh/Kafedra", "Fakultet", "Havola"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📄 PDF yuklash"):
                        st.download_button("Saqlash", generate_pdf(recs, role_f), f"{role_f}.pdf")
                with col2:
                    if st.button("Excel yuklash"):
                        st.download_button("Saqlash", generate_excel(df_view, role_f), f"{role_f}.xlsx")
                st.dataframe(df_view)
            else: st.info("Ma'lumot yo'q.")
            
        with tab1:
            df = pd.read_sql("SELECT role, faculty FROM data", conn)
            if not df.empty:
                st.bar_chart(df['faculty'].value_counts())

        with tab3:
            st.subheader("Fakultetlar")
            new_f = st.text_input("Yangi fakultet:")
            if st.button("Qo'shish") and new_f:
                c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                conn.commit()
                st.success("Qo'shildi!")

elif menu in ["Talaba", "O'qituvchi va xodim"]:
    st.header(f"{menu} anketasi")
    facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
    with st.form("anketa"):
        fio = st.text_input("F.I.O:")
        fac = st.selectbox("Fakultet:", facs)
        grp = st.text_input("Guruh/Kafedra:")
        lnk = st.text_input("Sertifikat linki:")
        if st.form_submit_button("Yuborish"):
            c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)",
                      (menu, fac, grp, fio, lnk))
            conn.commit()
            st.success("Saqlandi!")
else:
    st.title("Monitoring tizimi")
    st.write("Xush kelibsiz! Chap menyudan bo'limni tanlang.")
