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

# --- STYLE CSS (LUKSUSOWY INTERFEJS) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { 
        width: 100%; 
        border-radius: 15px; 
        height: 4em; 
        font-weight: 800; 
        font-size: 18px; 
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .men-badge { 
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%);
        border-left: 5px solid #2563eb; 
        color: #1e40af; 
        padding: 12px 20px; 
        border-radius: 10px; 
        font-weight: bold; 
        font-size: 14px; 
        margin-bottom: 25px;
    }
    
    /* Styl Luksusowej Karty A4 */
    .a4-paper {
        background-color: white;
        padding: 60px 70px;
        border-radius: 4px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.15);
        color: #1e293b;
        font-family: 'Times New Roman', Times, serif;
        font-size: 16px;
        line-height: 1.7;
        min-height: 1000px;
        border: 1px solid #e2e8f0;
        white-space: pre-wrap;
        margin: 20px auto;
        max-width: 900px;
    }
    .status-ok { color: #059669; font-weight: bold; }
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

# --- DIAMENTOWY PARSER 5.0 (ODPORNY NA WSZYSTKO) ---
def clean_ai_response(raw_text):
    raw_text = raw_text.strip()
    
    if raw_text.startswith("```"):
        raw_text = re.sub(r'^```[a-z]*\n', '', raw_text)
        raw_text = re.sub(r'\n```$', '', raw_text)
        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            if data.get("content"): return data["content"]
            if "choices" in data and data["choices"]:
                msg = data["choices"][0].get("message", {})
                if msg.get("content"): return msg["content"]
    except: pass

    if '"reasoning_content":' in raw_text and '"content":' not in raw_text:
        return "BŁĄD: AI wygenerowało tylko myśli. Spróbuj ponownie."

    content_match = re.search(r'"content"\s*:\s*"(.*)"\}?$', raw_text, re.DOTALL)
    if content_match:
        extracted = content_match.group(1)
        extracted = re.sub(r'","tool_calls":\[\].*$', '', extracted)
        extracted = re.sub(r'","role":"assistant".*$', '', extracted)
        return extracted.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t').strip()

    clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    clean_text = re.sub(r'^\{.*?"content"\s*:\s*"', '', clean_text, flags=re.DOTALL)
    if clean_text.endswith('"}'): clean_text = clean_text[:-2]
    
    return clean_text.replace('\\n', '\n').replace('\\"', '"').strip()

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    h = doc.add_heading(doc_type.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run(f"Data wygenerowania: ....................").italic = True

    doc.add_paragraph(f"Imię i nazwisko ucznia: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue
        if line.startswith('### ') or line.startswith('## ') or line.startswith('# '):
            clean_line = line.replace('#', '').strip()
            doc.add_heading(clean_line, level=2)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_formatted_run(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_formatted_run(p, line)
            
    doc.add_paragraph("\n" + "_" * 30)
    footer = doc.add_paragraph("Dokument opracowany przy wsparciu Asystenta Pedagoga AI (EduBox).")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_formatted_run(paragraph, text):
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
    st.title("🎓 Asystent Pedagoga Specjalnego PRO")
    st.markdown(f'<div class="men-badge">🏆 KLASA S: Analiza orzeczeń i profesjonalny wydruk</div>', unsafe_allow_html=True)
with col_head2:
    st.success("🤖 Status: **Gotowy do pracy**")

# --- PANEL BOCZNY ---
with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    if code.upper() == "KAWA2024": st.success("Odblokowano MERCEDESA!")
    else: st.warning("Tryb limitowany")
    st.markdown("---")
    st.info("**RODO:** Używaj inicjałów ucznia!")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

# --- FORMULARZ ---
tab1, tab2 = st.tabs(["📁 1. Wgrywanie i Dane", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("Główny problem i dane ucznia")
    diagnosis = st.text_area("❗ OKREŚLENIE PROBLEMU DZIECKA / GŁÓWNA DIAGNOZA:", placeholder="Opisz tutaj z czym uczeń ma problem (np. spektrum autyzmu, trudności z koncentracją, agresja, afazja...). To kluczowe dla AI!", height=150)
    
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a")
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
        
    with c2:
        st.subheader("Dokumentacja bazowa")
        files = st.file_uploader("Wgraj orzeczenie z Poradni (PDF, DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

    extra_context = st.text_area("Dodatkowe uwagi nauczyciela:", placeholder="Np. Uczeń bardzo lubi pociągi, szybko się nudzi przy pisaniu...", height=100)

    # --- AKCJA ---
    if st.button("⚙️ GENERUJ PEŁNY DOKUMENT (Klasa S)"):
        if not s_name: st.error("⚠️ Podaj imię ucznia!")
        elif not diagnosis: st.error("⚠️ Opisz problem dziecka!")
        else:
            with st.spinner("🚀 AI analizuje dokumenty i pisze pismo..."):
                full_raw_data = ""
                if files:
                    for f in files: full_raw_data += f"\n[PLIK: {f.name}]\n" + extract_text_from_file(f)
                usr_msg = f"""OPRACUJ DOKUMENT: {doc_type}
                DANE UCZNIA: {s_name}, {s_info}
                DIAGNOZA: {diagnosis}. PLIKI: {full_raw_data}. NOTATKI: {extra_context}."""

                payload = {
                    "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                    "model": "openai"
                }

                try:
                    # ROZCIĘTY LINK - TERAZ EDYTOR GO NIE ZEPSUJE!
                    czesc_1 = "https://"
                    czesc_2 = "text.pollinations.ai/"
                    target_url = czesc_1 + czesc_2
                    
                    res = requests.post(target_url, json=payload, timeout=120)
                    if res.ok:
                        final_doc = clean_ai_response(res.text)
                        st.session_state['generated_doc'] = final_doc
                        st.session_state['s_name'] = s_name
                        st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd i Wydruk'.")
                    else: st.error(f"Błąd połączenia: {res.status_code}")
                except Exception as e: st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc_text = st.session_state['generated_doc']
        st.subheader("📥 Eksport do Worda")
        word_buf = create_word_document(doc_text, doc_type, st.session_state['s_name'])
        
        st.download_button(
            label="📁 POBIERZ JAKO MICROSOFT WORD (.DOCX)",
            data=word_buf,
            file_name=f"dokument_{st.session_state['s_name']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary"
        )
        st.markdown("---")
        st.markdown("### 🖥️ Podgląd arkusza A4")
        st.markdown(f'<div class="a4-paper">{doc_text}</div>', unsafe_allow_html=True)
    else: st.info("Wypełnij dane w pierwszej zakładce i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI PRO © 2026 | System wsparcia pedagogicznego.")
