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

# --- CUSTOM CSS (DIZAYN VA FOUTER) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3em; 
        background: linear-gradient(45deg, #1E3A8A, #3B82F6); 
        color: white; 
        border: none; 
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    
    .header-box {
        padding: 40px;
        background: linear-gradient(135deg, #1e3a8a 0%, #581c87 100%);
        color: white;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    .card {
        padding: 20px;
        background: white;
        border-radius: 12px;
        border-left: 5px solid #3B82F6;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        min-height: 150px;
    }
    
    /* KATTA SHRIFTLI ESLATMA */
    .big-info {
        font-size: 32px !important; 
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        padding: 20px;
        background-color: #e7f0ff;
        border-radius: 10px;
        margin-top: 20px;
    }
    
    .footer { 
        position: fixed; 
        bottom: 10px; 
        left: 50%; 
        transform: translateX(-50%); 
        color: #888; 
        font-size: 14px; 
        font-weight: 500;
        z-index: 1000; 
        background: rgba(255,255,255,0.7);
        padding: 5px 20px;
        border-radius: 20px;
    }
    </style>
    <div class="footer">© 2026 Created by Odiljon Jakbarov</div>
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

# --- ASOSIY MENYU ---
menu = st.sidebar.selectbox("🚀 Bo'limni tanlang", ["Bosh sahifa", "Talaba 🎓", "O'qituvchi va xodim 👨‍🏫", "Administrator 🛠"])

if menu == "Bosh sahifa":
    st.markdown("""
        <div class="header-box">
            <h1>🤖 Sun'iy Intellekt Kursi Monitoringi</h1>
            <p style="font-size: 1.2em;">Sertifikatlar olinganligini raqamli nazorat qilish platformasi</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="card"><h3>🧠 Kurs Mazmuni</h3>
        Generativ AI, Prompt Engineering va Big Data yo'nalishlari bo'yicha sertifikatlar monitoringi.</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card"><h3>📜 Sertifikatlar</h3>
        Olingan sertifikat havolasini tizimga kiriting va muvaffaqiyatli ro'yxatdan o'ting.</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="card"><h3>⚡ Tezkorlik</h3>
        Ma'lumotlar xavfsiz bazada saqlanadi va hisobotlar avtomatik shakllanadi.</div>""", unsafe_allow_html=True)
    
    # KATTA SHRIFTDA ESLATMA
    st.markdown('<p class="big-info">👈 Davom etish uchun rolingizga mos bo\'limni tanlang.</p>', unsafe_allow_html=True)

elif menu == "Administrator 🛠":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "Jo12100105+":
        st.header("⚙ Boshqaruv paneli")
        tab1, tab2, tab3 = st.tabs(["📈 Statistika", "📋 Hisobotlar", "🔧 Sozlamalar"])
        # (Administrator qismi avvalgidek qoladi...)
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
                st.dataframe(df_view, use_container_width=True)
            else: st.info("Ma'lumot mavjud emas.")
            
        with tab3:
            st.subheader("Fakultetlarni tahrirlash")
            facs_list = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
            with st.expander("➕ Yangi qo'shish"):
                new_f = st.text_input("Nomi:")
                if st.button("Saqlash") and new_f:
                    c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                    conn.commit()
                    st.rerun()

elif "Talaba" in menu or "O'qituvchi" in menu:
    if "Talaba" in menu:
        header_text = "📝 Talaba sertifikatini yuklash oynasi"
        role_name = "Talaba"
    else:
        header_text = "📝 O'qituvchi va xodim sertifikatini yuklash oynasi"
        role_name = "O'qituvchi va xodim"

    st.markdown(f"### {header_text}")
    facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
    
    with st.form("reg_form"):
        fio = st.text_input("To'liq F.I.O:")
        fac = st.selectbox("Fakultetingiz:", facs)
        grp = st.text_input("Guruh yoki Kafedra:")
        lnk = st.text_input("Sertifikat linki:")
        if st.form_submit_button("✅ Ma'lumotni yuborish"):
            if fio and lnk:
                c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)",
                          (role_name, fac, grp, fio, lnk))
                conn.commit()
                st.balloons()
                st.success("Rahmat! Ma'lumotlaringiz qabul qilindi.")
            else: st.error("F.I.O va Link majburiy!")
