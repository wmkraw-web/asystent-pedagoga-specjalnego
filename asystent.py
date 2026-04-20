import streamlit as st
import moduly

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="wide")

# --- STYLE CSS (Globalne) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 16px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border: none;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .men-badge { 
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-left: 5px solid #2563eb; 
        color: #1e40af; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 14px; margin-bottom: 15px;
    }
    .a4-paper {
        background-color: white; border-radius: 5px; padding: 40px 60px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); color: #1e293b;
        font-family: 'Times New Roman', Times, serif; font-size: 16px;
        border: 1px solid #e2e8f0; margin: 10px auto; max-width: 850px; min-height: 800px;
    }
    .story-box { background-color: #fffbeb; padding: 25px; border-radius: 15px; border: 2px dashed #fcd34d; font-family: 'Comic Sans MS', sans-serif; font-size: 18px; line-height: 1.8; color: #451a03; }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBALNA INFORMACJA MEN ---
st.info("⚖️ **Zgodność z Prawem Oświatowym:** Narzędzia w tej aplikacji zostały zoptymalizowane do generowania treści (IPET, WOPFU, Scenariusze) w ścisłym oparciu o aktualne wytyczne Ministerstwa Edukacji Narodowej (MEN) oraz obowiązującą podstawę programową.")

# --- KLUCZE API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- MENU BOCZNE ---
with st.sidebar:
    st.title("🎓 EduBox")
    st.caption("Kombajn Modułowy v4.5 (Z grafiką i wydrukiem)")
    
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: 
        st.success("Premium Aktywne (DALL-E Odblokowane)")
    else:
        st.warning("Podaj aktywny kod aby odblokować generowanie zdjęć i profesjonalne dokumenty.")
    
    st.markdown("---")
    st.subheader("🛠️ Wybierz Narzędzie")
    
    narzedzie = st.radio("Menu Główne:", [
        "📑 Asystent Dokumentów (IPET)",
        "🧩 Historyjki Społeczne (+ Grafiki AI)",
        "🎈 Rymowanki Przedszkolne",
        "🎭 Kreator TUS",
        "🤝 Komunikacja z Rodzicem"
    ])
    
    st.markdown("---")
    st.markdown("""
        <a href="https://buycoffee.to/magiccolor" target="_blank" style="display: block; text-align: center;">
            <img src="https://buycoffee.to/btn/buycoffeeto-btn-primary.svg" style="width: 100%; max-width: 220px; margin: 0 auto; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s;" alt="Postaw mi kawę na buycoffee.to">
        </a>
    """, unsafe_allow_html=True)

# --- ROUTING (Przełączanie modułów z pliku moduly.py) ---
if narzedzie == "📑 Asystent Dokumentów (IPET)":
    moduly.modul_asystent_dokumentow(OPENAI_API_KEY, is_pro)

elif narzedzie == "🧩 Historyjki Społeczne (+ Grafiki AI)":
    moduly.modul_historyjki_spoleczne(OPENAI_API_KEY, is_pro)

elif narzedzie == "🎈 Rymowanki Przedszkolne":
    moduly.modul_przedszkole(OPENAI_API_KEY)

elif narzedzie == "🎭 Kreator TUS":
    moduly.modul_kreator_tus(OPENAI_API_KEY)

elif narzedzie == "🤝 Komunikacja z Rodzicem":
    moduly.modul_trudny_rodzic(OPENAI_API_KEY)
