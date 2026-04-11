import streamlit as st
import requests
import json
import re
import io
import time

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

# --- STYLE CSS (LUKSUSOWY INTERFEJS A4) ---
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
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE POMOCNICZE ---
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

def clean_ai_response(raw_text):
    raw_text = raw_text.strip()
    # Usuwanie bloków ```markdown / ```json
    raw_text = re.sub(r'^```[a-z]*\n', '', raw_text)
    raw_text = re.sub(r'\n```$', '', raw_text)
    
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            if data.get("content"): return data["content"]
            if "choices" in data:
                return data["choices"][0]["message"].get("content", "")
    except: pass

    # Jeśli AI wysłało surowy tekst z "reasoning_content", wycinamy tylko czysty content
    if '"content":' in raw_text:
        match = re.search(r'"content"\s*:\s*"(.*?)"(?=,"tool_calls"|\}$)', raw_text, re.DOTALL)
        if match:
            return match.group(1).replace('\\n', '\n').replace('\\"', '"')

    # Usuwanie tagów myślowych <think>
    return re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

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

# --- DANE MEN ---
MEN_RULES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura: Zakres dostosowań, działania specjalistów, formy pomocy PP, współpraca z rodzicami, ocena efektywności.",
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura: Potrzeby, mocne strony, przyczyny niepowodzeń, bariery, wnioski.",
    "Opinia o uczniu / Arkusz obserwacji": "Struktura: Funkcjonowanie poznawcze, społeczne, emocjonalne, zalecenia."
}

# --- UI ---
st.title("🎓 Asystent Pedagoga PRO")
st.markdown('<div class="men-badge">🏆 KLASA S: Automatyczna analiza i profesjonalny wydruk</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje PREMIUM")
    st.info("RODO: Używaj inicjałów ucznia!")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

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
        if not s_name or not diagnosis: st.error("⚠️ Podaj imię i diagnozę!")
        else:
            with st.spinner("🚀 Mercedes rusza... AI analizuje dokumenty. To może potrwać do 60s."):
                full_text = ""
                if files:
                    for f in files: full_text += f"\n[ANALIZA: {f.name}]\n" + extract_text_from_file(f)
                
                sys_msg = f"Jesteś ekspertem pedagogiki. Napisz profesjonalny dokument {doc_type} zgodnie z MEN. Używaj Markdown. Zwróć tylko czysty tekst dokumentu bez JSON."
                usr_msg = f"UCZEŃ: {s_name}, {s_info}. DIAGNOZA: {diagnosis}. NOTATKI: {extra}. PLIKI: {full_text[:5000]}"

                # HAKERSKIE ŁĄCZENIE LINKU (Ochrona przed formatowaniem czatu)
                p1, p2 = "https://", "text.pollinations.ai/"
                api_url = p1 + p2
                
                success = False
                for attempt in range(3): # PRÓBUJEMY 3 RAZY W RAZIE BŁĘDU 502
                    try:
                        res = requests.post(api_url, json={
                            "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                            "model": "openai"
                        }, timeout=90)
                        
                        if res.status_code == 200:
                            final_doc = clean_ai_response(res.text)
                            if len(final_doc) > 100: # Sprawdzamy czy to nie same myśli
                                st.session_state['generated_doc'] = final_doc
                                st.session_state['s_name'] = s_name
                                success = True
                                break
                        time.sleep(2) # Czekaj 2s przed ponowieniem
                    except: time.sleep(2)
                
                if success: st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd i Wydruk'.")
                else: st.error("❌ Serwer AI jest obecnie zbyt zajęty (Błąd 502). Spróbuj ponownie za minutę.")

with tab2:
    if 'generated_doc' in st.session_state:
        doc = st.session_state['generated_doc']
        st.download_button("📁 POBIERZ PLIK WORD (.DOCX)", create_word_document(doc, doc_type, st.session_state['s_name']), file_name=f"{st.session_state['s_name']}_dokument.docx", type="primary")
        st.markdown("---")
        html = markdown.markdown(doc, extensions=['tables'])
        st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else: st.info("Wypełnij dane i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI © 2026 | System wsparcia pedagoga.")
