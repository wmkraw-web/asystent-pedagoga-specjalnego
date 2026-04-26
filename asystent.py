import streamlit as st
import moduly

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga PRO - EduBox", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS (Dark Premium Mode) ---
st.markdown("""
    <style>
    /* Główne tło i tekst */
    .stApp { background-color: #020617; color: #f8fafc; }
    h1, h2, h3, h4, h5, h6 { color: #f8fafc !important; }
    
    /* Panel boczny (Glassmorphism) */
    [data-testid="stSidebar"] { 
        background-color: rgba(30, 41, 59, 0.6) !important; 
        backdrop-filter: blur(16px); 
        border-right: 1px solid rgba(255, 255, 255, 0.05); 
    }
    
    /* Przyciski Główne */
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: 800; font-size: 16px; 
        background: linear-gradient(135deg, #e11d48 0%, #be123c 100%); color: white; border: none;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(225, 29, 72, 0.3);
    }
    .stButton>button:hover { 
        transform: translateY(-2px); box-shadow: 0 8px 25px rgba(225, 29, 72, 0.5); color: white; border: none;
    }
    
    /* Pola tekstowe i inputy */
    .stTextInput>div>div>input, .stTextArea>div>textarea, .stNumberInput>div>div>input { 
        background-color: #0f172a; color: #f8fafc; border: 1px solid #334155; border-radius: 10px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>textarea:focus { 
        border-color: #e11d48; box-shadow: 0 0 10px rgba(225, 29, 72, 0.3); 
    }
    
    /* Selectboxy (Listy rozwijane) */
    div[data-baseweb="select"] > div { 
        background-color: #0f172a; color: #f8fafc; border-color: #334155; border-radius: 10px;
    }
    
    /* Alerty i Informacje */
    .men-badge { 
        background: rgba(225, 29, 72, 0.15); border-left: 4px solid #fb7185; 
        color: #fda4af; padding: 15px 20px; border-radius: 12px; font-weight: bold; font-size: 14px; 
        margin-bottom: 20px; border-top: 1px solid rgba(251, 113, 133, 0.2); border-right: 1px solid rgba(251, 113, 133, 0.2); border-bottom: 1px solid rgba(251, 113, 133, 0.2);
    }
    
    /* Wydruk: Biała Kartka A4 */
    .a4-paper {
        background-color: #ffffff; border-radius: 5px; padding: 40px 60px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5); color: #0f172a;
        font-family: 'Times New Roman', Times, serif; font-size: 16px;
        border: 1px solid #cbd5e1; margin: 20px auto; max-width: 850px; min-height: 800px;
    }
    .a4-paper h1, .a4-paper h2, .a4-paper h3, .a4-paper h4 { color: #0f172a !important; margin-top: 1.5em; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;}
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1em 0; }
    .a4-paper th, .a4-paper td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
    .a4-paper th { background-color: #f1f5f9; }
    
    /* Box na Historyjki */
    .story-box { background-color: rgba(30, 41, 59, 0.8); padding: 25px; border-radius: 15px; border: 2px dashed #e11d48; font-size: 18px; line-height: 1.8; color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBALNA INFORMACJA MEN ---
st.info("⚖️ **Zgodność z Prawem Oświatowym:** Narzędzia zoptymalizowane do generowania treści (IPET, WOPFU) w ścisłym oparciu o wytyczne MEN.")

# --- KLUCZE API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- MENU BOCZNE ---
with st.sidebar:
    st.title("🎓 EduBox")
    st.caption("Kombajn Modułowy v5.0 (Dark Premium)")
    
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: 
        st.success("🌟 Premium Aktywne (Moduły odblokowane)")
    else:
        st.warning("Podaj aktywny kod aby odblokować generowanie zdjęć i profesjonalne dokumenty urzędowe.")
    
    st.markdown("---")
    st.subheader("🛠️ Wybierz Narzędzie")
    
    narzedzie = st.radio("Menu Główne:", [
        "📑 Asystent Dokumentów (IPET/WOPFU)",
        "🧩 Historyjki Społeczne (+ Grafiki AI)",
        "🎈 Rymowanki Przedszkolne",
        "🎭 Kreator TUS",
        "🤝 Komunikacja z Rodzicem"
    ])
    
    st.markdown("---")
    st.markdown("""
        <a href="https://buycoffee.to/magiccolor" target="_blank" style="display: block; text-align: center;">
            <img src="https://buycoffee.to/btn/buycoffeeto-btn-primary.svg" style="width: 100%; max-width: 220px; margin: 0 auto; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s;" alt="Postaw mi kawę na buycoffee.to">
        </a>
    """, unsafe_allow_html=True)

# --- ROUTING (Przełączanie modułów z pliku moduly.py) ---
if narzedzie == "📑 Asystent Dokumentów (IPET/WOPFU)":
    moduly.modul_asystent_dokumentow(OPENAI_API_KEY, is_pro)

elif narzedzie == "🧩 Historyjki Społeczne (+ Grafiki AI)":
    moduly.modul_historyjki_spoleczne(OPENAI_API_KEY, is_pro)

elif narzedzie == "🎈 Rymowanki Przedszkolne":
    moduly.modul_przedszkole(OPENAI_API_KEY)

elif narzedzie == "🎭 Kreator TUS":
    moduly.modul_kreator_tus(OPENAI_API_KEY)

elif narzedzie == "🤝 Komunikacja z Rodzicem":
    moduly.modul_trudny_rodzic(OPENAI_API_KEY)
