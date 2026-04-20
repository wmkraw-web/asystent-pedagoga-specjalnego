import streamlit as st
import requests
import json
import io
import re

# --- IMPORTY BIBLIOTEK DOKUMENTÓW ---
try:
    import PyPDF2
except ImportError:
    st.error("Brak biblioteki PyPDF2. Dodaj 'PyPDF2' do pliku requirements.txt")
try:
    import docx
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    st.error("Brak biblioteki python-docx. Dodaj 'python-docx' do pliku requirements.txt")
try:
    import markdown
except ImportError:
    st.error("Brak biblioteki markdown. Dodaj 'markdown' do pliku requirements.txt")

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="EduBox - Kombajn Nauczyciela", page_icon="🎓", layout="wide")

# --- SPRAWDZENIE KLUCZA API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; font-size: 16px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .men-badge { 
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-left: 5px solid #2563eb; 
        color: #1e40af; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 14px; margin-bottom: 25px;
    }
    .a4-paper {
        background-color: white; padding: 50px 70px; border-radius: 5px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); color: #1e293b;
        font-family: 'Times New Roman', Times, serif; font-size: 16px;
        line-height: 1.6; min-height: 800px; border: 1px solid #e2e8f0;
        margin: 10px auto; max-width: 850px;
    }
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
    .a4-paper th, .a4-paper td { border: 1px solid #cbd5e1; padding: 12px; text-align: left; }
    .a4-paper th { background-color: #f8fafc; font-weight: bold; }
    .chat-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# FUNKCJE POMOCNICZE (WSPÓLNE DLA MODUŁÓW)
# ==========================================

def call_openai_api(system_prompt, user_prompt, temperature=0.6):
    if not OPENAI_API_KEY:
        return "Błąd: Brak klucza API OpenAI."
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": temperature
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        if response.ok:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Błąd API: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Błąd krytyczny komunikacji z API: {str(e)}"

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: 
                if para.text.strip(): text += para.text + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e: st.error(f"Błąd odczytu pliku: {e}")
    return text

def fix_markdown_tables(text):
    text = text.replace("[TUTAJ ZACZYNA SIĘ TABELA DO WYPEŁNIENIA]", "").replace("[KONIEC TABELI]", "")
    lines = text.split('\n')
    fixed_lines = []
    for i in range(len(lines)):
        fixed_lines.append(lines[i])
        if lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if not next_line.startswith('|--') and not next_line.startswith('| :--'):
                    cols = lines[i].count('|') - 1
                    separator = "|" + "---|" * cols
                    fixed_lines.append(separator)
    return "\n".join(fixed_lines)

# ==========================================
# MODUŁ 1: ASYSTENT DOKUMENTÓW (STARA CZĘŚĆ)
# ==========================================
def modul_asystent_dokumentow(is_pro):
    st.header("📝 Asystent Dokumentów (IPET, WOPFU)")
    st.markdown('<div class="men-badge">🏆 KLASA S: Urzędowe Formatowanie i Język Ekspercki</div>', unsafe_allow_html=True)
    
    MEN_RULES = {
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura: Zakres dostosowań, zintegrowane działania specjalistów...",
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania)": "Struktura: Indywidualne potrzeby, mocne strony, bariery...",
        "Opinia o uczniu / Arkusz obserwacji": "Struktura: Opis funkcjonowania poznawczego, społecznego i emocjonalnego...",
    }
    
    tab1, tab2 = st.tabs(["📁 Dane", "📄 Podgląd"])
    with tab1:
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
        template_file = st.file_uploader("Opcjonalnie: Wgraj własny wzór (.DOCX):", type=['docx'])
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Imię / Inicjały ucznia:")
            diagnosis = st.text_area("Diagnoza główna:", height=100)
        with c2:
            strengths = st.text_area("💪 Mocne strony:", height=100)
            weaknesses = st.text_area("🚧 Trudności:", height=100)
            
        if st.button("⚙️ GENERUJ DOKUMENT"):
            if not is_pro: st.error("Wymagany Kod Premium (KAWA2024)")
            elif not s_name or not diagnosis: st.warning("Podaj imię i diagnozę.")
            else:
                with st.spinner("Przetwarzam..."):
                    sys_prompt = f"Jesteś wybitnym diagnostą. Napisz {doc_type}. Używaj specjalistycznego żargonu pedagogicznego."
                    user_prompt = f"Imię: {s_name}\nDiagnoza: {diagnosis}\nMocne: {strengths}\nSłabe: {weaknesses}"
                    result = call_openai_api(sys_prompt, user_prompt, temperature=0.5)
                    st.session_state['gen_doc'] = fix_markdown_tables(result)
                    st.success("Gotowe! Przejdź do zakładki Podgląd.")
                    
    with tab2:
        if 'gen_doc' in st.session_state:
            html = markdown.markdown(st.session_state['gen_doc'], extensions=['tables'])
            st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
        else:
            st.info("Wygeneruj dokument w pierwszej zakładce.")

# ==========================================
# MODUŁ 2: TŁUMACZ - TRUDNY RODZIC (NOWOŚĆ!)
# ==========================================
def modul_trudny_rodzic():
    st.header("🤝 Tłumacz: Asystent Komunikacji z Rodzicem")
    st.markdown("Ten moduł zamienia Twoje emocjonalne myśli na uprzejmy, asertywny i profesjonalny komunikat gotowy do wysłania (np. przez e-dziennik Librus/Vulcan).")
    
    st.info("💡 **Przykład:** Zamiast *'Pani syn znowu kopie inne dzieci, zróbcie coś z tym!'*, AI napisze profesjonalną notatkę o trudnościach w samoregulacji z prośbą o współpracę.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        ton_wypowiedzi = st.selectbox("Wybierz cel i ton wiadomości:", [
            "Uprzejma prośba o interwencję (np. zachowanie)",
            "Stanowcze przypomnienie o zasadach (np. przyprowadzanie chorych dzieci)",
            "Zawiadomienie o problemach w nauce (motywacyjne)",
            "Zaproszenie na trudną rozmowę (dyplomatyczne)"
        ])
        
        surowy_tekst = st.text_area("Co chcesz przekazać rodzicowi? (Napisz swoimi słowami, nawet w nerwach):", height=200, 
                                    placeholder="Np. Pani syn znowu przyszedł chory. Ma gila do pasa i kaszle na całą grupę. Zabierzcie go, bo pozaraża resztę!")
        
        if st.button("✨ Przetłumacz na język dyplomacji"):
            if surowy_tekst:
                with st.spinner("Trwa redagowanie dyplomatycznej wiadomości..."):
                    sys_prompt = f"""Jesteś doświadczonym, empatycznym, ale bardzo asertywnym pedagogiem. 
                    Twoim zadaniem jest 'przetłumaczenie' pełnej emocji wiadomości nauczyciela na profesjonalny, uprzejmy komunikat do rodzica (np. na e-dziennik).
                    
                    CEL WIADOMOŚCI: {ton_wypowiedzi}
                    
                    ZASADY:
                    1. Bądź uprzejmy, ale stanowczy (tzw. metoda kanapki: pozytyw - problem - pozytyw/rozwiązanie).
                    2. Unikaj oskarżycielskiego tonu. Używaj języka korzyści (troska o dziecko i grupę).
                    3. Zwracaj się formalnie ("Szanowny Panie / Szanowna Pani").
                    4. Zaproponuj współpracę na linii dom-szkoła.
                    5. Zwróć sam gotowy tekst do skopiowania, bez żadnych wstępów."""
                    
                    gotowy_tekst = call_openai_api(sys_prompt, surowy_tekst, temperature=0.7)
                    st.session_state['tlumacz_wynik'] = gotowy_tekst
            else:
                st.warning("Wpisz najpierw swoją myśl!")

    with c2:
        if 'tlumacz_wynik' in st.session_state:
            st.markdown("### 📩 Gotowa wiadomość (do skopiowania):")
            st.markdown(f"<div class='chat-box'>{st.session_state['tlumacz_wynik']}</div>", unsafe_allow_html=True)
            
            # Przycisk do szybkiego kopiowania (tylko jako wizualny element w st, realne kopiowanie uzytkownik robi myszka)
            st.caption("Zaznacz tekst powyżej i skopiuj (Ctrl+C), aby wkleić do e-dziennika.")


# ==========================================
# POZOSTAŁE MODUŁY (W BUDOWIE)
# ==========================================
def modul_w_budowie(tytul, opis):
    st.header(f"🚧 {tytul}")
    st.info(opis)
    st.image("https://images.unsplash.com/photo-1503676260728-1c00da094a0b?q=80&w=2022&auto=format&fit=crop", caption="Moduł w fazie projektowania...", use_column_width=True)


# ==========================================
# GŁÓWNA STRUKTURA (MENU BOCZNE)
# ==========================================
with st.sidebar:
    st.title("🎓 EduBox")
    st.caption("Kombajn Nauczyciela v3.0")
    
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Premium Aktywne")
    
    st.markdown("---")
    st.subheader("🛠️ Wybierz Narzędzie")
    
    narzedzie = st.radio("Menu Główne:", [
        "📑 Asystent Dokumentów (IPET)",
        "🤝 Komunikacja z Rodzicem",
        "🧩 Historyjki Społeczne (Autyzm)",
        "🎭 Kreator TUS",
        "🎈 Przedszkole (Rymowanki)",
        "🧪 Projekty Badawcze"
    ])
    
    st.markdown("---")
    st.markdown("[☕ Postaw Kawę Twórcy](https://buycoffee.to/magiccolor)")


# ==========================================
# ROUTING (WYŚWIETLANIE WYBRANEGO NARZĘDZIA)
# ==========================================
if narzedzie == "📑 Asystent Dokumentów (IPET)":
    modul_asystent_dokumentow(is_pro)
    
elif narzedzie == "🤝 Komunikacja z Rodzicem":
    modul_trudny_rodzic()
    
elif narzedzie == "🧩 Historyjki Społeczne (Autyzm)":
    modul_w_budowie("Generator Historyjek Społecznych", "Wkrótce: Tworzenie terapeutycznych opowiadań krok po kroku dla dzieci w spektrum autyzmu.")
    
elif narzedzie == "🎭 Kreator TUS":
    modul_w_budowie("Kreator Zajęć TUS", "Wkrótce: Automatyczne generowanie scenariuszy Treningu Umiejętności Społecznych.")
    
elif narzedzie == "🎈 Przedszkole (Rymowanki)":
    modul_w_budowie("Asystent Przedszkolny", "Wkrótce: Wierszyki na dyplomy, rymowanki wyciszające i scenariusze dzienne zgodne z podstawą programową.")

elif narzedzie == "🧪 Projekty Badawcze":
    modul_w_budowie("Metoda Projektów", "Wkrótce: Generowanie pytań badawczych i eksperymentów dla przedszkolaków.")
