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
    .story-box { background-color: #fffbeb; padding: 30px; border-radius: 15px; border: 2px dashed #fcd34d; font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif; font-size: 18px; line-height: 1.8; color: #451a03; }
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
# MODUŁ 1: ASYSTENT DOKUMENTÓW (IPET, WOPFU)
# ==========================================
def modul_asystent_dokumentow(is_pro):
    st.header("📝 Asystent Dokumentów (IPET, WOPFU)")
    st.markdown('<div class="men-badge">🏆 KLASA S: Urzędowe Formatowanie i Język Ekspercki</div>', unsafe_allow_html=True)
    
    MEN_RULES = {
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura: Zakres dostosowań, zintegrowane działania specjalistów...",
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania)": "Struktura: Indywidualne potrzeby, mocne strony, bariery...",
        "Opinia o uczniu do Poradni PPP": "Struktura: Opis funkcjonowania poznawczego, społecznego, emocjonalnego. Ton obiektywny, nieoceniający, bazujący na faktach.",
    }
    
    tab1, tab2 = st.tabs(["📁 Dane", "📄 Podgląd"])
    with tab1:
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
        template_file = st.file_uploader("Opcjonalnie: Wgraj własny wzór (.DOCX):", type=['docx'])
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Imię / Inicjały ucznia:")
            diagnosis = st.text_area("Diagnoza główna / Powód opinii:", height=100)
        with c2:
            strengths = st.text_area("💪 Mocne strony:", height=100)
            weaknesses = st.text_area("🚧 Trudności / Niepokojące zachowania:", height=100)
            
        if st.button("⚙️ GENERUJ DOKUMENT"):
            if not is_pro: st.error("Wymagany Kod Premium (KAWA2024)")
            elif not s_name or not diagnosis: st.warning("Podaj imię i diagnozę.")
            else:
                with st.spinner("Przetwarzam fachowym żargonem..."):
                    sys_prompt = f"Jesteś wybitnym diagnostą i pedagogiem. Napisz dokument: {doc_type}. Używaj wysoce specjalistycznego żargonu pedagogicznego i psychologicznego. Jeśli to opinia do PPP, zachowaj maksymalny obiektywizm."
                    user_prompt = f"Imię: {s_name}\nDiagnoza: {diagnosis}\nMocne: {strengths}\nSłabe: {weaknesses}\nWymagania: {MEN_RULES[doc_type]}"
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
# MODUŁ 2: TŁUMACZ - TRUDNY RODZIC
# ==========================================
def modul_trudny_rodzic():
    st.header("🤝 Tłumacz: Komunikacja z Rodzicem")
    st.markdown("Ten moduł zamienia Twoje emocjonalne myśli na uprzejmy, asertywny i profesjonalny komunikat.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        ton_wypowiedzi = st.selectbox("Wybierz cel i ton wiadomości:", [
            "Uprzejma prośba o interwencję (np. zachowanie)",
            "Stanowcze przypomnienie o zasadach (np. przyprowadzanie chorych dzieci)",
            "Zawiadomienie o problemach w nauce (motywacyjne)",
            "Zaproszenie na trudną rozmowę (dyplomatyczne)"
        ])
        
        surowy_tekst = st.text_area("Co chcesz przekazać rodzicowi? (Napisz swoimi słowami, prosto z mostu):", height=150, 
                                    placeholder="Np. Pani syn znowu przyszedł chory. Ma gila do pasa i kaszle. Zabierzcie go!")
        
        if st.button("✨ Przetłumacz na język dyplomacji"):
            if surowy_tekst:
                with st.spinner("Redagowanie wiadomości..."):
                    sys_prompt = f"Jesteś empatycznym, asertywnym pedagogiem. Przetłumacz emocjonalny tekst na profesjonalną, formalną wiadomość e-dziennika. Cel: {ton_wypowiedzi}. Metoda kanapki (pozytyw-problem-pozytyw). Zwróć tylko gotowy tekst."
                    st.session_state['tlumacz_wynik'] = call_openai_api(sys_prompt, surowy_tekst, temperature=0.7)
            else: st.warning("Wpisz najpierw swoją myśl!")

    with c2:
        if 'tlumacz_wynik' in st.session_state:
            st.markdown("### 📩 Gotowa wiadomość (do skopiowania):")
            st.markdown(f"<div class='chat-box'>{st.session_state['tlumacz_wynik']}</div>", unsafe_allow_html=True)


# ==========================================
# MODUŁ 3: HISTORYJKI SPOŁECZNE (AUTYZM)
# ==========================================
def modul_historyjki_spoleczne():
    st.header("🧩 Generator Historyjek Społecznych")
    st.markdown("Tworzy terapeutyczne opowiadania krok po kroku (Social Stories) dla dzieci w spektrum autyzmu.")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        imie = st.text_input("Imię dziecka:")
        wiek = st.number_input("Wiek dziecka:", min_value=2, max_value=15, value=5)
        problem = st.text_area("Sytuacja problemowa / Zapalnik (Trigger):", placeholder="Np. Zosia bardzo boi się dźwięku szkolnego dzwonka lub odkurzacza.")
        rozwiazanie = st.text_area("Oczekiwana reakcja / Strategia (Opcjonalnie):", placeholder="Np. Zakładamy słuchawki wyciszające, robimy głęboki wdech.")
        
        if st.button("📖 Wygeneruj Historyjkę"):
            if imie and problem:
                with st.spinner("Pisanie historyjki społecznej..."):
                    sys_prompt = f"""Jesteś certyfikowanym terapeutą behawioralnym. Twoim zadaniem jest napisanie Historyjki Społecznej (Carol Gray) dla {wiek}-letniego dziecka w spektrum autyzmu.
                    ZASADY KRYTYCZNE:
                    1. Używaj języka hiper-dosłownego, prostego. ŻADNYCH przenośni, ironii i metafor.
                    2. Zachowaj klasyczną strukturę:
                       - Zdania opisowe (fakty: Kto, co, gdzie).
                       - Zdania perspektywiczne (Co czują inni, co czuje dziecko).
                       - Zdania dyrektywne (Co dokładnie dziecko ma zrobić krok po kroku).
                       - Zdania afirmujące (Pozytywne wzmocnienie).
                    3. Tekst sformatuj w bardzo krótkich akapitach, by nauczyciel mógł łatwo dodać obrazki do każdego z nich."""
                    
                    user_prompt = f"Imię: {imie}\nProblem: {problem}\nSugerowane rozwiązanie: {rozwiazanie}"
                    st.session_state['historyjka_wynik'] = call_openai_api(sys_prompt, user_prompt, temperature=0.5)
            else: st.warning("Wpisz imię i opisz problem.")

    with c2:
        if 'historyjka_wynik' in st.session_state:
            st.markdown("### 📚 Twoja Historyjka:")
            st.markdown(f"<div class='story-box'>{st.session_state['historyjka_wynik']}</div>", unsafe_allow_html=True)
            st.info("💡 Wskazówka: Wydrukuj tekst, rozetnij na kawałki i poproś dziecko o narysowanie (lub wygeneruj w Magic Color AI) obrazków do każdego akapitu!")


# ==========================================
# MODUŁ 4: KREATOR TUS
# ==========================================
def modul_kreator_tus():
    st.header("🎭 Kreator Zajęć TUS (Trening Umiejętności Społecznych)")
    st.markdown("Generuje praktyczne scenariusze zajęć skupione na konkretnym problemie grupy.")
    
    col1, col2 = st.columns(2)
    with col1:
        wiek = st.text_input("Wiek grupy (np. 6-7 lat):")
        czas = st.selectbox("Czas trwania zajęć:", ["30 minut", "45 minut", "60 minut", "90 minut"])
        cel = st.text_area("Główny problem do przepracowania:", placeholder="Np. Agresywne zachowania po przegranej w grze planszowej. Trudność z czekaniem na swoją kolej.")
        
        if st.button("🧩 Generuj Scenariusz TUS"):
            if cel and wiek:
                with st.spinner("Tworzenie konspektu TUS..."):
                    sys_prompt = """Jesteś ekspertem i trenerem Treningu Umiejętności Społecznych (TUS). Skonstruuj wysoce praktyczny scenariusz zajęć dla wskazanej grupy.
                    STRUKTURA (Użyj pogrubień dla sekcji):
                    1. Powitanie i Rytuał Początkowy (Rozładowanie napięcia)
                    2. Psychoedukacja (Proste wprowadzenie do tematu)
                    3. Scenki / Odgrywanie Ról (Trening właściwy - opisz 2 konkretne sytuacje do odegrania)
                    4. Trening relaksacyjny / wyciszenie
                    5. Pożegnanie i nagroda/wzmocnienie pozytywne
                    
                    Używaj punktów i podawaj szacowany czas na każdy etap."""
                    user_prompt = f"Wiek: {wiek}\nCzas: {czas}\nProblem do przepracowania: {cel}"
                    st.session_state['tus_wynik'] = call_openai_api(sys_prompt, user_prompt, temperature=0.6)
            else: st.warning("Wypełnij wiek i cel zajęć.")
            
    with col2:
        if 'tus_wynik' in st.session_state:
            st.markdown("### 📋 Twój Scenariusz TUS:")
            st.markdown(f"<div class='a4-paper' style='min-height:500px; padding:30px;'>{st.session_state['tus_wynik']}</div>", unsafe_allow_html=True)


# ==========================================
# MODUŁ 5: ASYSTENT PRZEDSZKOLNY
# ==========================================
def modul_przedszkole():
    st.header("🎈 Asystent Przedszkolny (Rymowanki i Dyplomy)")
    st.markdown("Ratunek w codziennej pracy z maluchami: wierszyki wyciszające, rymowanki dyplomowe i więcej.")
    
    typ = st.radio("Czego potrzebujesz?", ["Wierszyk na Dyplom (Dla konkretnego dziecka)", "Rymowanka grupowa (Zarządzanie grupą/Zabawa paluszkowa)"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if "Dyplom" in typ:
            imie = st.text_input("Imię dziecka:")
            cechy = st.text_area("Za co nagroda / Cechy dziecka:", placeholder="Np. Ukończenie przedszkola. Jasio uwielbia dinozaury, zawsze ma uśmiech na twarzy i pięknie rysuje.")
        else:
            temat = st.text_area("Jaki jest cel rymowanki?", placeholder="Np. Krótka rymowanka o sprzątaniu zabawek z pokazywaniem gestów. Dla 3-latków.")
            
        if st.button("✍️ Wymyśl Wierszyk"):
            with st.spinner("Układanie rymów..."):
                sys_prompt = "Jesteś najbardziej kreatywnym nauczycielem przedszkola na świecie. Piszesz genialne, bardzo rytmiczne rymowanki i wierszyki dla dzieci. Dbaj o dokładne rymy (najlepiej AABB lub ABAB) oraz stały rytm i liczbę sylab w wersach, aby dzieciom łatwo było je skandować."
                if "Dyplom" in typ:
                    user_prompt = f"Napisz wesoły 4-6 wersowy wierszyk na dyplom dla dziecka. Imię: {imie}. Kontekst/Cechy: {cechy}."
                else:
                    user_prompt = f"Napisz rytmiczną rymowankę użytkową dla grupy przedszkolnej. Cel/Temat: {temat}. Dodaj w nawiasach instrukcje gestów (np. klaskanie, tupanie) dla nauczyciela."
                
                st.session_state['przedszkole_wynik'] = call_openai_api(sys_prompt, user_prompt, temperature=0.8)

    with c2:
        if 'przedszkole_wynik' in st.session_state:
            st.markdown("### 🎵 Twój Wierszyk:")
            st.markdown(f"<div class='story-box' style='background-color:#f0fdf4; border-color:#86efac;'>{st.session_state['przedszkole_wynik'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)


# ==========================================
# MODUŁ 6: PROJEKTY BADAWCZE
# ==========================================
def modul_projekty_badawcze():
    st.header("🧪 Kreator Metody Projektów Badawczych")
    st.markdown("Rozpisuje kompleksowe, innowacyjne projekty edukacyjne dla przedszkoli i młodszych klas na całe tygodnie.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        temat = st.text_input("Temat projektu (np. Woda, Kosmos, Krowa):")
        wiek = st.text_input("Wiek dzieci:")
        czas = st.selectbox("Szacowany czas trwania:", ["1 tydzień", "2 tygodnie", "1 miesiąc"])
        
        if st.button("🔍 Opracuj Projekt"):
            if temat:
                with st.spinner("Projektowanie działań badawczych..."):
                    sys_prompt = """Jesteś wybitnym metodykiem edukacji wczesnoszkolnej i przedszkolnej, pasjonatem "Metody Projektów" według Lilian Katz.
                    Opracuj plan projektu badawczego dla dzieci. 
                    
                    WYMAGANA STRUKTURA:
                    **Etap 1: Rozpoczęcie Projektu**
                    - Sposób wzbudzenia zaciekawienia (tzw. prowokacja, np. tajemnicze pudełko).
                    - Przykładowa siatka pytań dzieci (Czego chcemy się dowiedzieć?).
                    
                    **Etap 2: Działania Badawcze (Główna część)**
                    - Zaproponuj 3 angażujące eksperymenty lub praktyczne zadania badawcze.
                    - Kogo zaprosić w roli eksperta? (np. strażak, weterynarz).
                    
                    **Etap 3: Zakończenie Projektu**
                    - Propozycja wydarzenia kulminacyjnego podsumowującego zdobytą wiedzę.
                    - Sposób włączenia i zaprezentowania efektów rodzicom."""
                    
                    user_prompt = f"Temat: {temat}\nWiek dzieci: {wiek}\nCzas trwania: {czas}"
                    st.session_state['projekt_wynik'] = call_openai_api(sys_prompt, user_prompt, temperature=0.7)
            else: st.warning("Podaj temat projektu!")

    with col2:
        if 'projekt_wynik' in st.session_state:
            st.markdown("### 🗺️ Plan Projektu Badawczego:")
            st.markdown(f"<div class='a4-paper' style='min-height:500px; padding:30px; font-family:sans-serif;'>{st.session_state['projekt_wynik']}</div>", unsafe_allow_html=True)


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
    else: st.warning("Niektóre funkcje mogą być zablokowane.")
    
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
    modul_historyjki_spoleczne()
elif narzedzie == "🎭 Kreator TUS":
    modul_kreator_tus()
elif narzedzie == "🎈 Przedszkole (Rymowanki)":
    modul_przedszkole()
elif narzedzie == "🧪 Projekty Badawcze":
    modul_projekty_badawcze()
