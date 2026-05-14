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
st.set_page_config(page_title="AI Monitoring Platform", layout="wide", page_icon="🤖")

# --- CUSTOM CSS (DIZAYN) ---
st.markdown("""
    <style>
    /* Asosiy fon va shriftlar */
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background: linear-gradient(45deg, #1E3A8A, #3B82F6); color: white; border: none; }
    
    /* Header qismi */
    .header-box {
        padding: 40px;
        background: linear-gradient(135deg, #1e3a8a 0%, #581c87 100%);
        color: white;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* Kartochkalar */
    .card {
        padding: 20px;
        background: white;
        border-radius: 12px;
        border-left: 5px solid #3B82F6;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    .footer { position: fixed; right: 20px; bottom: 20px; color: #888; font-size: 12px; z-index: 1000; }
    </style>
    <div class="footer">Created by Jakbarov Odiljon</div>
    """, unsafe_allow_html=True)

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('university_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, faculty TEXT, 
                  dept_group TEXT, fio TEXT, cert_link TEXT)''')
    c.execute("PRAGMA table_info(data)")
    cols = [column[1] for column in c.fetchall()]
    if 'cert_link' not in cols:
        try:
            c.execute("ALTER TABLE data ADD COLUMN cert_link TEXT")
            conn.commit()
        except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS faculties (name TEXT UNIQUE)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- PDF/EXCEL FUNKSIYALARI (O'zgarmadi) ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    elements.append(Paragraph(f"Hisobot: {title}", title_style))
    table_data = [["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat"]]
    for row in records: table_data.append([str(x) if x else "Yo'q" for x in row])
    t = Table(table_data, colWidths=[6*cm, 5*cm, 6*cm, 8*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.blue), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

def generate_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Hisobot")
    return output.getvalue()

# --- ASOSIY LOGIKA ---
menu = st.sidebar.selectbox("🚀 Menyu", ["Bosh sahifa", "Talaba 🎓", "O'qituvchi ва xodim 👨‍🏫", "Administrator 🛠"])

if menu == "Bosh sahifa":
    st.markdown("""
        <div class="header-box">
            <h1>🤖 Sun'iy Intellekt Kursi Monitoringi</h1>
            <p style="font-size: 1.2em;">Raqamli kelajak sari bir qadam!</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="card"><h3>🧠 Kurs Maqsadi</h3>
        Sun'iy intellekt va Prompt Engineering asoslarini o'rganish orqali samaradorlikni oshirish.</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card"><h3>📜 Sertifikat</h3>
        Kursni muvaffaqiyatli yakunlab, xalqaro darajadagi platformalar sertifikatini yuklang.</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="card"><h3>📊 Monitoring</h3>
        Fakultetlar va xodimlarning o'zlashtirish darajasini real vaqtda kuzatib boring.</div>""", unsafe_allow_html=True)
    
    st.info("👈 Davom etish uchun chap tomondagi menyudan o'z rolingizni tanlang.")

elif menu == "Administrator 🛠":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "Jo12100105+":
        st.header("⚙ Boshqaruv paneli")
        tab1, tab2, tab3 = st.tabs(["📈 Statistika", "📋 Hisobotlar", "🔧 Sozlamalar"])
        
        with tab1:
            df_stat = pd.read_sql("SELECT role, faculty FROM data", conn)
            if not df_stat.empty:
                st.subheader("Fakultetlar kesimida faollik")
                st.bar_chart(df_stat['faculty'].value_counts())
        
        with tab2:
            role_f = st.radio("Toifa:", ["O'qituvchi va xodim", "Talaba"], horizontal=True)
            c.execute("SELECT fio, dept_group, faculty, cert_link FROM data WHERE role=?", (role_f,))
            recs = c.fetchall()
            if recs:
                df_view = pd.DataFrame(recs, columns=["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat"])
                st.download_button("📥 Excel yuklash", generate_excel(df_view, role_f), f"{role_f}.xlsx")
                st.dataframe(df_view, use_container_width=True)
            else: st.info("Hozircha ma'lumot yo'q.")
            
        with tab3:
            st.subheader("Fakultetlar bazasi")
            new_f = st.text_input("Yangi fakultet nomi:")
            if st.button("Qo'shish") and new_f:
                c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                conn.commit()
                st.success("Baza yangilandi!")
                st.rerun()

elif "Talaba" in menu or "O'qituvchi" in menu:
    role_name = "Talaba" if "Talaba" in menu else "O'qituvchi va xodim"
    st.markdown(f"### 📝 {role_name} anketasi")
    facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
    
    with st.form("reg_form"):
        fio = st.text_input("To'liq F.I.O:")
        fac = st.selectbox("Fakultetni tanlang:", facs)
        grp = st.text_input("Guruh / Kafedra / Bo'lim:")
        lnk = st.text_input("Sertifikat linki (Google Drive, LinkedIn va h.k.):")
        
        if st.form_submit_button("✅ Ma'lumotni yuborish"):
            if fio and lnk:
                c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)",
                          (role_name, fac, grp, fio, lnk))
                conn.commit()
                st.balloons()
                st.success("Ma'lumotlaringiz muvaffaqiyatli qabul qilindi!")
            else: st.error("Iltimos, barcha maydonlarni to'ldiring!")
