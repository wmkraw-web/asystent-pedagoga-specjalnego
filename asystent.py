import streamlit as st
import requests
import json
import re
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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="wide")

# --- STYLE CSS (EFEKT A4) ---
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: 800; font-size: 16px; transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .men-badge { background-color: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; padding: 8px 12px; border-radius: 8px; font-weight: bold; font-size: 12px; text-transform: uppercase; margin-bottom: 20px; display: inline-block;}
    
    /* Styl Karty A4 na podglądzie */
    .a4-paper {
        background-color: white;
        padding: 40px 50px;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        color: #1e293b;
        font-family: 'Times New Roman', Times, serif;
        font-size: 15px;
        line-height: 1.6;
        min-height: 800px;
        border: 1px solid #e2e8f0;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE (ODCZYT PLIKÓW) ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Nie udało się odczytać pliku {uploaded_file.name}: {e}")
    return text

# --- OSTATECZNY PARSER AI ---
def clean_ai_response(raw_text):
    raw_text = raw_text.strip()
    
    # Próba odczytania surowego tekstu, jeśli AI wysłało czysty string
    if not raw_text.startswith('{') and not raw_text.startswith('```'):
        return re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

    # Usunięcie bloków kodu, jeśli AI ubrało JSON w markdown
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text.strip("`").strip()
        
    # 1. Próba eleganckiego odczytania JSON
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            if "content" in data:
                return data["content"]
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                return msg.get("content", "")
    except json.JSONDecodeError:
        pass

    # 2. Ręczne wyciąganie tekstu z uszkodzonego JSON-a
    if '"content":"' in raw_text:
        start_idx = raw_text.find('"content":"') + 11
        content_str = raw_text[start_idx:]
        
        # Odcinamy końcówki systemowe
        if '","tool_calls":' in content_str:
            content_str = content_str.split('","tool_calls":')[0]
        elif content_str.endswith('"}'):
            content_str = content_str[:-2]
            
        # Zamiana technicznych znaków ucieczki
        content_str = content_str.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
        return content_str.strip()

    # 3. Jeśli nie było JSON-a, wycinamy tylko tagi myślowe
    clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    return clean_text.strip()

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    heading = doc.add_heading(doc_type, level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Dotyczy ucznia: {student_name}").bold = True
    doc.add_paragraph("_" * 60)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue
            
        if line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_formatted_text(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_formatted_text(p, line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_formatted_text(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0:
            run.bold = True

# --- SZABLONY WYMOGÓW MEN ---
MEN_TEMPLATES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": """
        1. Zakres i sposób dostosowania wymagań edukacyjnych.
        2. Zintegrowane działania nauczycieli i specjalistów.
        3. Formy i okres udzielania pomocy psychologiczno-pedagogicznej.
        4. Działania wspierające rodziców ucznia.
        5. Ocenę efektywności programu.
    """,
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": """
        1. Indywidualne potrzeby rozwojowe i edukacyjne oraz możliwości psychofizyczne.
        2. Mocne strony, predyspozycje, zainteresowania i uzdolnienia.
        3. Przyczyny niepowodzeń edukacyjnych lub trudności w funkcjonowaniu.
        4. Bariery i ograniczenia utrudniające funkcjonowanie ucznia.
        5. Wnioski do dalszej pracy.
    """,
    "Opinia o uczniu / Arkusz obserwacji": """
        1. Funkcjonowanie poznawcze ucznia.
        2. Funkcjonowanie emocjonalno-społeczne (relacje z rówieśnikami, zachowanie).
        3. Samodzielność i motoryka.
        4. Trudności dydaktyczne.
        5. Mocne strony i zalecenia do pracy.
    """
}

# --- INTERFEJS ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("🎓 Asystent Pedagoga PRO")
    st.markdown('<div class="men-badge">✓ Algorytm zgodny z wytycznymi MEN</div>', unsafe_allow_html=True)
    st.markdown("Wykorzystaj potęgę AI do analizy orzeczeń z Poradni Psychologiczno-Pedagogicznej.")
with col_head2:
    st.info("💡 **PRO TIP:** Wgraj skan diagnozy (PDF), a AI samo wyciągnie z niego wnioski!")

st.markdown("---")

with st.sidebar:
    st.header("🔒 Panel Kontrolny")
    access_code = st.text_input("Kod dostępu Premium:", type="password")
    is_premium = False
    if access_code.upper() == "KAWA2024":
        is_premium = True
        st.success("✅ Wersja PRO aktywna!")
    
    st.markdown("---")
    st.warning("🛡️ **RODO:** Używaj inicjałów ucznia!")
    st.markdown("[☕ Postaw Kawę Twórcy](https://buycoffee.to/magiccolor)")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📂 1. Dane i Dokumenty")
    student_name = st.text_input("Imię / Inicjały ucznia:", placeholder="np. Jan K.")
    student_age = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2b")
    doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_TEMPLATES.keys()))
    uploaded_files = st.file_uploader("Wgraj orzeczenie/opinię (PDF, DOCX)", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    
with col2:
    st.markdown("### 🎯 2. Wytyczne")
    diagnosis = st.text_input("Główna Diagnoza (jeśli brak pliku):", placeholder="np. Spektrum autyzmu...")
    context = st.text_area("Dodatkowe notatki nauczyciela:", height=150)
    st.info(f"📚 **Wymogi MEN:**\n{MEN_TEMPLATES[doc_type]}")

# --- GENERATOR ---
if st.button("⚙️ GENERUJ DOKUMENT (Analiza AI)", type="primary"):
    if not uploaded_files and not diagnosis.strip() and not context.strip():
        st.error("⚠️ Podaj dane wejściowe!")
    else:
        with st.spinner("🤖 Opracowuję profesjonalny dokument..."):
            extracted_text = ""
            if uploaded_files:
                for file in uploaded_files:
                    extracted_text += f"\n--- PLIK: {file.name} ---\n{extract_text_from_file(file)}\n"
            
            system_msg = f"""Jesteś ekspertem pedagogiki specjalnej w Polsce. Opracuj dokument ({doc_type}).
            Bezwzględna zgodność z MEN. Styl formalny, pedagogiczny.
            PUNKTY OBOWIĄZKOWE: {MEN_TEMPLATES[doc_type]}
            Zwróć TYLKO dokument w Markdown. Żadnego JSON-a."""

            user_msg = f"DANE: {student_name}, {student_age}. DIAGNOZA: {diagnosis}. NOTATKI: {context}. TEKST PLIKÓW: {extracted_text}"

            payload = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "model": "openai" 
            }

            try:
                # NAPRAWIONY ADRES URL - CZYSTY LINK
                response = requests.post("https://text.pollinations.ai/", json=payload, timeout=60)
                
                if response.ok:
                    raw_result = response.text
                    final_doc = clean_ai_response(raw_result)
                    
                    st.success("✅ Dokument przygotowany!")
                    
                    docx_buffer = create_word_document(final_doc, doc_type, student_name)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.download_button(
                            label="📥 POBIERZ PLIK WORD (.DOCX)",
                            data=docx_buffer,
                            file_name=f"{student_name}_dokument.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )
                    
                    st.markdown("#### Podgląd wydruku:")
                    st.markdown(f'<div class="a4-paper">{final_doc}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Serwer AI zwrócił błąd: {response.status_code}")
            except Exception as e:
                st.error(f"Błąd krytyczny: {str(e)}")

st.markdown("---")
st.caption("EduBox AI © 2026 | Mercedes Klasy S wśród asystentów pedagoga.")
