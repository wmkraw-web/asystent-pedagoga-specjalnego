imporimport streamlit as st
import requests
import json
import io

# --- IMPORTY BIBLIOTEK DOKUMENTÓW ---
try:
    import PyPDF2
except ImportError:
    st.error("Brak biblioteki PyPDF2. Dodaj 'PyPDF2' do pliku requirements.txt")
try:
    import docx
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    st.error("Brak biblioteki python-docx. Dodaj 'python-docx' do pliku requirements.txt")
try:
    import markdown
except ImportError:
    st.error("Brak biblioteki markdown. Dodaj 'markdown' do pliku requirements.txt")

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="wide")

# --- SPRAWDZENIE KLUCZA API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- STYLE CSS (LUKSUSOWY INTERFEJS) ---
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 4em; font-weight: 800; font-size: 18px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2); }
    .men-badge { 
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-left: 5px solid #2563eb; 
        color: #1e40af; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 14px; margin-bottom: 25px;
    }
    .a4-paper {
        background-color: white; padding: 50px 70px; border-radius: 2px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.1); color: #1e293b;
        font-family: 'Times New Roman', Times, serif; font-size: 15px;
        line-height: 1.6; min-height: 1000px; border: 1px solid #e2e8f0;
        margin: 10px auto; max-width: 850px;
    }
    .a4-paper h1, .a4-paper h2, .a4-paper h3 { color: #0f172a; margin-top: 1.5em; border-bottom: 1px solid #eee; }
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1em 0; }
    .a4-paper th, .a4-paper td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .a4-paper th { background-color: #f9fafb; }
    .status-ok { color: #059669; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE (ODCZYT PLIKÓW) ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e: st.error(f"Błąd odczytu pliku: {e}")
    return text

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    h = doc.add_heading(doc_type.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Uczeń: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line: doc.add_paragraph(); continue
        if line.startswith('### ') or line.startswith('## ') or line.startswith('# '):
            doc.add_heading(line.replace('#', '').strip(), level=2)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_bold_parts(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_bold_parts(p, line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_bold_parts(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- BAZA WIEDZY MEN ---
MEN_RULES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura musi zawierać: Zakres dostosowań, zintegrowane działania specjalistów, formy pomocy PP, współpracę z rodzicami oraz ocenę efektywności.",
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura musi zawierać: Indywidualne potrzeby, mocne strony, przyczyny niepowodzeń, bariery środowiskowe oraz wnioski do pracy.",
    "Opinia o uczniu / Arkusz obserwacji": "Struktura musi zawierać: Opis funkcjonowania poznawczego, społecznego i emocjonalnego oraz zalecenia.",
    "Własny Dokument / Inny (Zgodnie z szablonem placówki)": "Wygeneruj dokument ściśle według szablonu podanego przez użytkownika w polu 'Szablon placówki'."
}

# --- INTERFEJS UŻYTKOWNIKA ---
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.title("🎓 Asystent Pedagoga PRO")
    st.markdown('<div class="men-badge">🏆 KLASA S: Automatyczna analiza i profesjonalny wydruk</div>', unsafe_allow_html=True)
with col_head2:
    if OPENAI_API_KEY:
        st.success("🤖 Połączenie API: **Aktywne**")
    else:
        st.error("🔴 Brak Klucza API w ustawieniach Secrets!")

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje PREMIUM")
    st.markdown("---")
    st.info("RODO: Używaj inicjałów ucznia!")

tab1, tab2 = st.tabs(["📁 1. Dane i Pliki", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("1. Główny Problem / Diagnoza")
    diagnosis = st.text_area("❗ GŁÓWNA DIAGNOZA / OPIS TRUDNOŚCI:", placeholder="Np. Spektrum autyzmu, trudności z koncentracją, afazja...", height=80)
    
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a")
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
    with c2:
        files = st.file_uploader("Wgraj orzeczenia z Poradni (PDF/DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

    st.markdown("---")
    st.subheader("2. Szczegółowe informacje o uczniu")
    c3, c4 = st.columns(2)
    with c3:
        strengths = st.text_area("💪 Mocne strony i zasoby (Potencjał):", placeholder="Np. chętnie pomaga innym, dobrze radzi sobie z matematyką, ma dobrą pamięć wzrokową, lubi zajęcia plastyczne...", height=100)
    with c4:
        weaknesses = st.text_area("🚧 Trudności i bariery (Dysfunkcje):", placeholder="Np. problemy z koncentracją uwagi, szybko się zniechęca przy niepowodzeniach, trudności w nawiązywaniu relacji rówieśniczych...", height=100)

    st.markdown("---")
    st.subheader("3. Wymogi Twojej placówki (Opcjonalnie)")
    custom_template = st.text_area("📋 Wklej wzór / strukturę wymaganą w Twojej szkole:", placeholder="Masz konkretny wzór? Wklej tu puste nagłówki (np. 1. Zachowanie, 2. Postępy, 3. Zalecenia). \nMożesz też wpisać: 'Proszę wygenerować zalecenia w formie tabeli z 3 kolumnami: Cel, Metoda, Sposób realizacji'. AI dostosuje się do Ciebie!", height=120)

    if st.button("⚙️ GENERUJ DOKUMENT"):
        if not OPENAI_API_KEY:
            st.error("⚠️ Brak skonfigurowanego klucza OpenAI w Streamlit Secrets!")
        elif not s_name or not diagnosis:
            st.error("⚠️ Podaj imię i diagnozę główną!")
        else:
            with st.spinner("🚀 AI weryfikuje dane, tworzy tabele i pisze dokument... To zajmie ok. 15 sekund."):
                full_text = ""
                if files:
                    for f in files: full_text += f"\n[ANALIZA: {f.name}]\n" + extract_text_from_file(f)
                
                # LOGIKA SZABLONU: Jeśli użytkownik wkleił własny szablon, AI traktuje go priorytetowo
                template_instruction = f"WYMAGANA STRUKTURA DOKUMENTU OD DYREKCJI: Należy BEZWZGLĘDNIE zastosować poniższy układ/tabelę i wypełnić go treścią:\n{custom_template}" if custom_template.strip() else f"WYMAGANIA MEN: {MEN_RULES[doc_type]}"

                sys_msg = f"""Jesteś ekspertem pedagogiki specjalnej i wybitnym diagnostą w Polsce. Twoim zadaniem jest napisanie profesjonalnego dokumentu ({doc_type}).
                ZASADY:
                1. {template_instruction}
                2. Styl formalny, urzędowy, obiektywny. Używaj fachowej terminologii psychologiczno-pedagogicznej.
                3. Wykorzystaj podane przez użytkownika zasoby i bariery ucznia do wyciągnięcia logicznych zaleceń do pracy.
                4. Zwróć TYLKO czysty tekst dokumentu w formacie Markdown (jeśli użytkownik prosił o tabelę, użyj formatowania tabeli Markdown). Żadnego wstępu i zakończenia typu 'Oto twój dokument'."""

                usr_msg = f"""DANE UCZNIA: {s_name}, {s_info}
                DIAGNOZA GŁÓWNA: {diagnosis}
                MOCNE STRONY (Zasoby): {strengths if strengths.strip() else 'Brak szczegółowych danych'}
                TRUDNOŚCI (Bariery): {weaknesses if weaknesses.strip() else 'Brak szczegółowych danych'}
                PLIKI DO ANALIZY: {full_text[:15000]}"""

                try:
                    headers = {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": "gpt-4o-mini", 
                        "messages": [
                            {"role": "system", "content": sys_msg},
                            {"role": "user", "content": usr_msg}
                        ],
                        "temperature": 0.4
                    }
                    
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
                    
                    if response.ok:
                        data = response.json()
                        final_doc = data["choices"][0]["message"]["content"]
                        
                        st.session_state['generated_doc'] = final_doc
                        st.session_state['s_name'] = s_name
                        st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd i Wydruk'.")
                    else:
                        error_data = response.json()
                        st.error(f"Błąd OpenAI: {error_data.get('error', {}).get('message', 'Nieznany błąd')}")
                        
                except Exception as e: 
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc = st.session_state['generated_doc']
        st.download_button("📁 POBIERZ PLIK WORD (.DOCX)", create_word_document(doc, doc_type, st.session_state['s_name']), file_name=f"{st.session_state['s_name']}_dokument.docx", type="primary")
        st.markdown("---")
        html = markdown.markdown(doc, extensions=['tables'])
        st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else: st.info("Wypełnij dane i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI © 2026 | Powered by OpenAI GPT-4o-mini")t streamlit as st
import requests
import json
import io

# --- IMPORTY BIBLIOTEK DOKUMENTÓW ---
try:
    import PyPDF2
except ImportError:
    st.error("Brak biblioteki PyPDF2. Dodaj 'PyPDF2' do pliku requirements.txt")
try:
    import docx
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    st.error("Brak biblioteki python-docx. Dodaj 'python-docx' do pliku requirements.txt")
try:
    import markdown
except ImportError:
    st.error("Brak biblioteki markdown. Dodaj 'markdown' do pliku requirements.txt")

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="wide")

# --- SPRAWDZENIE KLUCZA API ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = None

# --- STYLE CSS (LUKSUSOWY INTERFEJS) ---
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 4em; font-weight: 800; font-size: 18px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2); }
    .men-badge { 
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%); border-left: 5px solid #2563eb; 
        color: #1e40af; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 14px; margin-bottom: 25px;
    }
    .a4-paper {
        background-color: white; padding: 50px 70px; border-radius: 2px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.1); color: #1e293b;
        font-family: 'Times New Roman', Times, serif; font-size: 15px;
        line-height: 1.6; min-height: 1000px; border: 1px solid #e2e8f0;
        margin: 10px auto; max-width: 850px;
    }
    .a4-paper h1, .a4-paper h2, .a4-paper h3 { color: #0f172a; margin-top: 1.5em; border-bottom: 1px solid #eee; }
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1em 0; }
    .a4-paper th, .a4-paper td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .a4-paper th { background-color: #f9fafb; }
    .status-ok { color: #059669; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE (ODCZYT PLIKÓW) ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e: st.error(f"Błąd odczytu pliku: {e}")
    return text

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    h = doc.add_heading(doc_type.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Uczeń: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line: doc.add_paragraph(); continue
        if line.startswith('### ') or line.startswith('## ') or line.startswith('# '):
            doc.add_heading(line.replace('#', '').strip(), level=2)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_bold_parts(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_bold_parts(p, line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_bold_parts(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- BAZA WIEDZY MEN ---
MEN_RULES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura musi zawierać: Zakres dostosowań, zintegrowane działania specjalistów, formy pomocy PP, współpracę z rodzicami oraz ocenę efektywności.",
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura musi zawierać: Indywidualne potrzeby, mocne strony, przyczyny niepowodzeń, bariery środowiskowe oraz wnioski do pracy.",
    "Opinia o uczniu / Arkusz obserwacji": "Struktura musi zawierać: Opis funkcjonowania poznawczego, społecznego i emocjonalnego oraz zalecenia."
}

# --- INTERFEJS UŻYTKOWNIKA ---
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.title("🎓 Asystent Pedagoga PRO")
    st.markdown('<div class="men-badge">🏆 KLASA S: Automatyczna analiza i profesjonalny wydruk</div>', unsafe_allow_html=True)
with col_head2:
    if OPENAI_API_KEY:
        st.success("🤖 Połączenie API: **Aktywne**")
    else:
        st.error("🔴 Brak Klucza API w ustawieniach Secrets!")

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje PREMIUM")
    st.markdown("---")
    st.info("RODO: Używaj inicjałów ucznia!")

tab1, tab2 = st.tabs(["📁 1. Dane i Pliki", "📝 2. Podgląd i Wydruk"])

with tab1:
    diagnosis = st.text_area("❗ OKREŚLENIE PROBLEMU / DIAGNOZA:", placeholder="Np. Spektrum autyzmu, trudności z koncentracją...", height=100)
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a")
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
    with c2:
        files = st.file_uploader("Wgraj orzeczenie (PDF/DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    extra = st.text_area("Dodatkowe uwagi:", height=80)

    if st.button("⚙️ GENERUJ DOKUMENT"):
        if not OPENAI_API_KEY:
            st.error("⚠️ Brak skonfigurowanego klucza OpenAI w Streamlit Secrets!")
        elif not s_name or not diagnosis:
            st.error("⚠️ Podaj imię i diagnozę!")
        else:
            with st.spinner("🚀 Weryfikacja danych i pisanie dokumentu... To zajmie ok. 15 sekund."):
                full_text = ""
                if files:
                    for f in files: full_text += f"\n[ANALIZA: {f.name}]\n" + extract_text_from_file(f)
                
                sys_msg = f"Jesteś ekspertem pedagogiki. Napisz profesjonalny dokument {doc_type} zgodnie z MEN: {MEN_RULES[doc_type]}. Styl formalny, urzędowy. Używaj formatowania Markdown."
                usr_msg = f"UCZEŃ: {s_name}, {s_info}. DIAGNOZA: {diagnosis}. NOTATKI: {extra}. PLIKI DO ANALIZY: {full_text[:15000]}"

                try:
                    # BEZPOŚREDNIE POŁĄCZENIE Z OFICJALNYM API OPENAI
                    headers = {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": "gpt-4o-mini", # Bardzo szybki, mądry i ekstremalnie tani model
                        "messages": [
                            {"role": "system", "content": sys_msg},
                            {"role": "user", "content": usr_msg}
                        ],
                        "temperature": 0.4
                    }
                    
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
                    
                    if response.ok:
                        data = response.json()
                        final_doc = data["choices"][0]["message"]["content"]
                        
                        st.session_state['generated_doc'] = final_doc
                        st.session_state['s_name'] = s_name
                        st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd i Wydruk'.")
                    else:
                        error_data = response.json()
                        st.error(f"Błąd OpenAI: {error_data.get('error', {}).get('message', 'Nieznany błąd')}")
                        
                except Exception as e: 
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc = st.session_state['generated_doc']
        st.download_button("📁 POBIERZ PLIK WORD (.DOCX)", create_word_document(doc, doc_type, st.session_state['s_name']), file_name=f"{st.session_state['s_name']}_dokument.docx", type="primary")
        st.markdown("---")
        html = markdown.markdown(doc, extensions=['tables'])
        st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else: st.info("Wypełnij dane i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI © 2026 | Powered by OpenAI GPT-4o-mini")
