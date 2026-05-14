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

# --- SHRIFT SOZLAMALARI (PDF uchun) ---
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
    
    # Ustunni tekshirish va xavfsiz qo'shish
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
    .footer { position: fixed; right: 20px; bottom: 20px; color: #888; font-weight: bold; z-index: 1000; background: rgba(255,255,255,0.8); padding: 5px 15px; border-radius: 8px; border: 1px solid #ddd; }
    </style>
    <div class="footer">Created by Jakbarov Odiljon</div>
    """, unsafe_allow_html=True)

# --- PDF VA EXCEL GENERATSIYA ---
def generate_pdf(records, title):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontName = FONT_NAME
    elements.append(Paragraph(f"Hisobot: {title}", title_style))
    
    table_data = [["F.I.O", "Guruh/Kafedra", "Fakultet", "Sertifikat havolasi"]]
    for row in records:
        table_data.append([str(x) if x else "Yo'q" for x in row])
    
    t = Table(table_data, colWidths=[6*cm, 5*cm, 6*cm, 8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    doc.build(elements)
    return buf.getvalue()

def generate_excel(df, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Hisobot")
    return output.getvalue()

# --- ASOSIY MENYU ---
menu = st.sidebar.selectbox("Bo'limni tanlang:", ["Bosh sahifa", "Talaba", "O'qituvchi va xodim", "Administrator"])

if 'access' not in st.session_state:
    st.session_state.access = True

if menu == "Administrator":
    pwd = st.sidebar.text_input("Parol:", type="password")
    if pwd == "Jo12100105+":
        st.header("🛠 Administrator paneli")
        st.session_state.access = st.toggle("Ro'yxatga olishni yopish/ochish", value=st.session_state.access)
        
        tab1, tab2, tab3 = st.tabs(["📊 Statistika", "📋 Hisobot yuklash", "⚙ Sozlamalar"])
        
        with tab1:
            data_df = pd.read_sql("SELECT role, faculty, dept_group FROM data", conn)
            if not data_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Xodimlar faolligi")
                    t_data = data_df[data_df['role'] == "O'qituvchi va xodim"]['faculty'].value_counts()
                    if not t_data.empty:
                        fig, ax = plt.subplots()
                        t_data.plot(kind='bar', color='#1E3A8A', ax=ax)
                        st.pyplot(fig)
                with col2:
                    st.subheader("Talabalar faolligi")
                    s_data = data_df[data_df['role'] == 'Talaba']['faculty'].value_counts()
                    if not s_data.empty:
                        fig2, ax2 = plt.subplots()
                        s_data.plot(kind='bar', color='#10B981', ax=ax2)
                        st.pyplot(fig2)
        
        with tab2:
            role_f = st.radio("Kimlar bo'yicha:", ["O'qituvchi va xodim", "Talaba"], horizontal=True)
            # Hisobot imkoniyatlarini to'liq tiklash
            query = "SELECT fio, dept_group, faculty, cert_link FROM data WHERE role=?"
            try:
                c.execute(query, (role_f,))
                recs = c.fetchall()
            except:
                c.execute("SELECT fio, dept_group, faculty, 'Yo''q' as cert_link FROM data WHERE role=?", (role_f,))
                recs = c.fetchall()
            
            if recs:
                df_view = pd.DataFrame(recs, columns=["F.I.O", "Guruh/Kafedra", "Fakultet", "Havola"])
                
                col_pdf, col_xl = st.columns(2)
                with col_pdf:
                    pdf_bytes = generate_pdf(recs, role_f)
                    st.download_button("📄 PDF formatda yuklash", pdf_bytes, f"{role_f}_hisobot.pdf", "application/pdf")
                
                with col_xl:
                    xl_bytes = generate_excel(df_view, role_f)
                    st.download_button("Excel formatda yuklash", xl_bytes, f"{role_f}_hisobot.xlsx")
                
                st.divider()
                st.dataframe(df_view, use_container_width=True)
            else:
                st.info("Hozircha ma'lumot mavjud emas.")

        with tab3:
            st.subheader("Fakultetlarni boshqarish")
            with st.expander("➕ Yangi fakultet qo'shish"):
                new_f = st.text_input("Nomini yozing:")
                if st.button("Saqlash"):
                    if new_f:
                        c.execute("INSERT OR IGNORE INTO faculties (name) VALUES (?)", (new_f,))
                        conn.commit()
                        st.success("Qo'shildi!")
                        st.rerun()

            with st.expander("✏️ Fakultet nomini tahrirlash"):
                facs_list = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
                old_name = st.selectbox("Tahrirlash uchun tanlang:", facs_list)
                new_name = st.text_input("Yangi nom:", value=old_name)
                if st.button("Yangilash"):
                    c.execute("UPDATE faculties SET name = ? WHERE name = ?", (new_name, old_name))
                    c.execute("UPDATE data SET faculty = ? WHERE faculty = ?", (new_name, old_name))
                    conn.commit()
                    st.success("Yangilandi!")
                    st.rerun()

            with st.expander("🗑 Fakultetni o'chirish"):
                facs_list_del = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
                del_fac = st.selectbox("O'chirish uchun tanlang:", facs_list_del, key="del_box")
                if st.button("O'chirish"):
                    c.execute("DELETE FROM faculties WHERE name = ?", (del_fac,))
                    conn.commit()
                    st.warning("O'chirildi.")
                    st.rerun()

elif menu in ["Talaba", "O'qituvchi va xodim"]:
    if st.session_state.access:
        st.header(f"{menu} anketasi")
        facs = [r[0] for r in c.execute("SELECT name FROM faculties").fetchall()]
        with st.form("main_form"):
            f_fio = st.text_input("F.I.O (To'liq):")
            f_fac = st.selectbox("Fakultet:", facs)
            f_group = st.text_input("Guruh yoki Kafedra:")
            f_link = st.text_input("Sertifikat havolasi (Link):")
            if st.form_submit_button("Yuborish"):
                if f_fio and f_link:
                    c.execute("INSERT INTO data (role, faculty, dept_group, fio, cert_link) VALUES (?,?,?,?,?)",
                              (menu, f_fac, f_group, f_fio, f_link))
                    conn.commit()
                    st.success("Muvaffaqiyatli saqlandi!")
                else: st.error("Majburiy maydonlarni to'ldiring!")
    else: st.error("Tizim vaqtincha yopiq.")
else:
    st.title("Universitet SI kursi monitoringi")
    st.info("Chap menyudan bo'limni tanlang.")
