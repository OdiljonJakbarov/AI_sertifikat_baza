import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import io

# --- SAHIFA SOZLAMALARI ----
st.set_page_config(page_title="AI Monitoring Platform", layout="wide", page_icon="🤖")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3em; 
        background: linear-gradient(45deg, #1E3A8A, #3B82F6); 
        color: white; border: none; transition: 0.3s;
    }
    .header-box {
        padding: 40px; background: linear-gradient(135deg, #1e3a8a 0%, #581c87 100%);
        color: white; border-radius: 15px; text-align: center; margin-bottom: 30px;
    }
    .card {
        padding: 20px; background: white; border-radius: 12px;
        border-left: 5px solid #3B82F6; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px; min-height: 150px;
    }
    .big-info {
        font-size: 32px !important; font-weight: bold; color: #1E3A8A;
        text-align: center; padding: 20px; background-color: #e7f0ff;
        border-radius: 10px; margin-top: 20px;
    }
    .footer { 
        position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); 
        color: #888; font-size: 14px; font-weight: 500; z-index: 1000; 
        background: rgba(255,255,255,0.7); padding: 5px 20px; border-radius: 20px;
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
    
    # 1. ESKI BARCHA FAKULTETLARNI O'CHIRIB TASHLOVCHI TOZALASH BU_YRUG'I
    c.execute("DELETE FROM faculties") 
    
    # 2. FAQAT SIZ AYTGAN YANGI LOTINCHA NOMULAR RO'YXATI
    fixed_faculties = [
        "Muhandislik-axborot texnologiyalari",
        "Transport",
        "Biznesni boshqarish",
        "Iqtisodiyot",
        "Qurilish",
        "Texnologiya",
        "Energetika",
        "Mexanika",
        "To‘qimachilik sanoati injineringi",
        "Bolimlar"
    ]
    
    # Yangi ro'yxatni bazaga yozish
    for fac in fixed_faculties:
        c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (fac,))
        
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- GENERATSIYA FUNKSIYALARI ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Hisobot: {title}", styles['Title']))
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
    with col1: st.markdown('<div class="card"><h3>🧠 Kurs Mazmuni</h3>Generativ AI va Prompt Engineering sertifikatlari monitoringi.</div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="card"><h3>📜 Sertifikatlar</h3>Sertifikat havolasini tizimga kiriting va ro\'yxatdan o\'ting.</div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="card"><h3>⚡ Tezkorlik</h3>Ma\'lumotlar xavfsiz bazada saqlanadi va hisobotlar tayyorlanadi.</div>', unsafe_allow_html=True)
    st.markdown('<p class="big-info">👈 Davom etish uchun rolingizga mos bo\'limni tanlang.</p>', unsafe_allow_html=True)

elif menu == "Administrator 🛠":
    pwd = st.sidebar.text_input("Administrator parolini kiriting:", type="password")
    if pwd == "Jo12100105+ ":
        st.header("🛠 Administrator boshqaruv paneli")
        tab1, tab2, tab3 = st.tabs(["📈 Statistika", "📋 Hisobotlar va Excel", "⚙ Fakultetlar sozlamalari"])
        
        with tab1:
            df_stat = pd.read_sql("SELECT faculty FROM data", conn)
            if not df_stat.empty:
                st.bar_chart(df_stat['faculty'].value_counts())
            else: st.info("Hozircha statistika yo'q.")
        
        with tab2:
            st.subheader("📋 Kiritilgan ma'lumotlarni ko'rish va yuklab olish")
            role_f = st.radio("Toifani tanlang:", ["O'qituvchi va xodim", "Talaba"], horizontal=True)
            
            c.execute("SELECT fio, dept_group, faculty, cert_link FROM data WHERE role=?", (role_f,))
            recs = c.fetchall()
            
            if recs:
                df_view = pd.DataFrame(recs, columns=["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat"])
            else:
                df_view = pd.DataFrame(columns=["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat"])
            
            col1, col2 = st.columns(2)
            with col1: 
                st.download_button(
                    label="📥 Экрандаги маълумотларни Excel файлда юклаб олиш", 
                    data=generate_excel(df_view, role_f), 
                    file_name=f"{role_f}_hisobot.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col2: 
                if recs: st.download_button("📄 PDF файлда юклаб олиш", generate_pdf(recs, role_f), f"{role_f}_hisobot.pdf")
                else: st.button("📄 PDF (Ma'lumot yo'q)", disabled=True)
            
            st.write("### Экрандаги жорий маълумотlar жадвали:")
            st.dataframe(df_view, use_container_width=True)

        with tab3:
            st.subheader("⚙ Fakultetlarni tahrirlash")
            facs_list = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
            with st.expander("➕ Yangi fakultet qo'shish"):
                n_f = st.text_input("Nomi:")
                if st.button("Qo'shish") and n_f:
                    c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (n_f,))
                    conn.commit(); st.rerun()
            if facs_list:
                with st.expander("✏️ Nomini o'zgartirish"):
                    old = st.selectbox("Tanlang:", facs_list)
                    new = st.text_input("Yangi nom:", value=old)
                    if st.button("Yangilash"):
                        c.execute("UPDATE faculties SET name=? WHERE name=?", (new, old))
                        c.execute("UPDATE data SET faculty=? WHERE faculty=?", (new, old))
                        conn.commit(); st.rerun()
                with st.expander("🗑 O'chirish"):
                    if st.button("Tanlangan fakultetni o'chirish"):
                        c.execute("DELETE FROM faculties WHERE name=?", (old,))
                        conn.commit(); st.rerun()
    elif pwd != "":
        st.sidebar.error("Parol noto'g'ri!")

elif "Talaba" in menu or "O'qituvchi" in menu:
    role_name = "Talaba" if "Talaba" in menu else "O'qituvchi va xodim"
    h_text = f"📝 {role_name} sertifikatini yuklash oynasi"
    st.markdown(f"### {h_text}")
    
    facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
    
    if not facs: st.warning("Fakultetlar qo'shilmagan.")
    else:
        with st.form("reg_form"):
            fio = st.text_input("To'liq F.I.O:")
            fac = st.selectbox("Fakultetingiz:", facs)
            input_label = "Ustozlar - kafedra nomini, Xodimlar - bolim nomini, Talabalar - guruh nomini kiriting:"
            grp = st.text_input(input_label)
            lnk = st.text_input("Sertifikat linki:")
            if st.form_submit_button("✅ Yuborish"):
                if fio and lnk:
                    c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)", (role_name, fac, grp, fio, lnk))
                    conn.commit(); st.balloons(); st.success("Qabul qilindi!")
                else: st.error("Maydonlarni to'ldiring!")
