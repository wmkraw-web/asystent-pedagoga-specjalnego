import streamlit as st
import moduly

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="EduBox - Kombajn Nauczyciela", page_icon="🎓", layout="wide")

# --- STYLE CSS (Globalne) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 16px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border: none;
    }
    .a4-paper {
        background-color: white; border-radius: 5px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); color: #1e293b;
        font-family: 'Times New Roman', Times, serif; font-size: 16px;
        border: 1px solid #e2e8f0; margin: 10px auto; max-width: 850px;
    }
    .story-box { background-color: #fffbeb; padding: 25px; border-radius: 15px; border: 2px dashed #fcd34d; font-family: 'Comic Sans MS', sans-serif; font-size: 18px; line-height: 1.8; color: #451a03; }
    </style>
    """, unsafe_allow_html=True)

# --- KLUCZE API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- MENU BOCZNE ---
with st.sidebar:
    st.title("🎓 EduBox")
    st.caption("Kombajn Modułowy v4.0")
    
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Premium Aktywne (Grafiki DALL-E Włączone)")
    
    st.markdown("---")
    st.subheader("🛠️ Wybierz Narzędzie")
    
    narzedzie = st.radio("Menu Główne:", [
        "🧩 Historyjki Społeczne (+ Grafiki AI)",
        "🎈 Rymowanki Przedszkolne",
        "🎭 Kreator TUS",
        "🧪 Projekty Badawcze"
    ])

# --- ROUTING (Przełączanie modułów) ---
if narzedzie == "🧩 Historyjki Społeczne (+ Grafiki AI)":
    moduly.modul_historyjki_spoleczne(OPENAI_API_KEY, is_pro)

elif narzedzie == "🎈 Rymowanki Przedszkolne":
    moduly.modul_przedszkole(OPENAI_API_KEY)

elif narzedzie == "🎭 Kreator TUS":
    moduly.modul_kreator_tus(OPENAI_API_KEY)

elif narzedzie == "🧪 Projekty Badawcze":
    moduly.modul_projekty_badawcze(OPENAI_API_KEY)
