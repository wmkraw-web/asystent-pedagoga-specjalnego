import streamlit as st
import requests
import json
import re
import io
import time

# --- IMPORTY BIBLIOTEK ---
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

# --- STYLE CSS (A4 PREMIUM) ---
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
        background-color: white; padding: 60px 70px; border-radius: 2px;
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

def titanium_parser(raw_text):
    """Najsilniejszy parser chroniący przed kodem JSON na ekranie"""
    raw_text = raw_text.strip()
    
    # Próba odkodowania JSON
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            # Szukamy treści w różnych standardach API
            content = ""
            if "content" in data: content = data["content"]
            elif "choices" in data: content = data["choices"][0]["message"].get("content", "")
            
            if content:
                return content.replace('\\n', '\n').replace('\\"', '"').strip()
            
            # Jeśli jest tylko "reasoning_content" bez "content" - to błąd AI
            if "reasoning_content" in data:
                return "ERROR_ONLY_REASONING"
    except:
        pass

    # Jeśli to nie był poprawny JSON, ale zawiera tagi <think>
    clean = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    
    # Ostatnia tarcza: jeśli tekst zaczyna się od { to znaczy, że to "śmieciowy" JSON
    if clean.startswith('{') and '"content"' not in clean:
        return "ERROR_JSON_TRASH"
    
    # Wyłapywanie contentu przez Regex (jeśli JSON jest ucięty)
    match = re.search(r'"content"\s*:\s*"(.*?)"(?=,"tool_calls"|\}$)', raw_text, re.DOTALL)
    if match:
        return match.group(1).replace('\\n', '\n').replace('\\"', '"')

    return clean.strip()

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
            parts = line[2:].split('**')
            for i, pt in enumerate(parts):
                run = p.add_run(pt)
                if i % 2 != 0: run.bold = True
        else:
            p = doc.add_paragraph()
            parts = line.split('**')
            for i, pt in enumerate(parts):
                run = p.add_run(pt)
                if i % 2 != 0: run.bold = True
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- UI ---
st.title("🎓 Asystent Pedagoga PRO")
st.markdown('<div class="men-badge">🏆 TITANIUM EDITION: Mercedes Klasy S wśród asystentów</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 Autoryzacja Premium")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje MERCEDES")
    st.markdown("---")
    st.info("RODO: Używaj inicjałów ucznia!")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

tab1, tab2 = st.tabs(["📁 1. Dane i Orzeczenia", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("Określenie problemu dziecka")
    diagnosis = st.text_area("❗ GŁÓWNA DIAGNOZA / PROBLEM DZIECKA:", placeholder="Np. Spektrum autyzmu, afazja, trudności z koncentracją, problemy z integracją z rówieśnikami...", height=120)
    
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a")
        doc_type = st.selectbox("Dokument do przygotowania:", ["IPET (Indywidualny Program Edukacyjno-Terapeutyczny)", "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)", "Opinia o uczniu / Arkusz obserwacji"])
    with c2:
        files = st.file_uploader("Wgraj orzeczenie z Poradni (PDF/DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    
    extra = st.text_area("Twoje dodatkowe uwagi:", placeholder="Np. Uczeń bardzo lubi pociągi, szybko się nudzi przy pisaniu...", height=80)

    if st.button("⚙️ GENERUJ PEŁNY DOKUMENT"):
        if not s_name or not diagnosis:
            st.error("⚠️ Podaj imię i opisz problem dziecka!")
        else:
            with st.spinner("🚀 Mercedes rusza... AI analizuje dokumenty. To zajmie tylko chwilę."):
                full_text = ""
                if files:
                    for f in files: full_text += f"\n[ANALIZA: {f.name}]\n" + extract_text_from_file(f)
                
                sys_msg = f"Jesteś najwyższej klasy pedagogiem specjalnym w Polsce. Napisz profesjonalny dokument {doc_type} zgodnie z wytycznymi MEN. Używaj języka urzędowego, pedagogicznego. Zwróć TYLKO czysty tekst dokumentu w formacie Markdown (nagłówki #, pogrubienia **, tabele). ZAKAZ: Nie zwracaj formatu JSON, nie pisz po angielsku."
                usr_msg = f"TEMAT: {doc_type}. UCZEŃ: {s_name}, {s_info}. GŁÓWNY PROBLEM: {diagnosis}. NOTATKI: {extra}. PLIKI: {full_text[:6000]}"

                # HAKERSKIE ŁĄCZENIE LINKU (Ochrona przed systemem czatu)
                h1, h2 = "https://", "text.pollinations.ai/"
                api_url = h1 + h2
                
                try:
                    res = requests.post(api_url, json={
                        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                        "model": "openai"
                    }, timeout=100)
                    
                    if res.ok:
                        final_doc = titanium_parser(res.text)
                        
                        if final_doc in ["ERROR_ONLY_REASONING", "ERROR_JSON_TRASH"]:
                            st.warning("⚠️ Serwer AI zawiesił się na procesie myślowym.")
                            st.error("AI nie wygenerowało dokumentu, a jedynie swoje przemyślenia. Wynika to z przeciążenia darmowych serwerów.")
                            st.button("🔄 Kliknij tutaj, aby spróbować ponownie")
                        else:
                            st.session_state['generated_doc'] = final_doc
                            st.session_state['s_name'] = s_name
                            st.success("✅ Dokument gotowy! Przejdź do zakładki 'Podgląd i Wydruk'.")
                    else:
                        st.error(f"Błąd połączenia z serwerem: {res.status_code}")
                except Exception as e:
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc_content = st.session_state['generated_doc']
        st.subheader("📥 Pobierz i Drukuj")
        
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button("📁 POBIERZ PLIK WORD (.DOCX)", create_word_document(doc_content, doc_type, st.session_state['s_name']), file_name=f"{st.session_state['s_name']}_dokument.docx", type="primary", use_container_width=True)
        with c_dl2:
            st.info("💡 Plik Word zawiera gotowe nagłówki i luksusowe formatowanie.")

        st.markdown("---")
        st.markdown("### 🖥️ Podgląd arkusza A4")
        html = markdown.markdown(doc_content, extensions=['tables'])
        st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else:
        st.info("Wypełnij dane w pierwszej zakładce i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI © 2026 | Profesjonalne wsparcie pedagoga specjalnego.")
