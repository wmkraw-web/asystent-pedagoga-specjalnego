import streamlit as st
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

# --- STYLE CSS ---
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
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1em 0; border: 1px solid #ddd; }
    .a4-paper th, .a4-paper td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .a4-paper th { background-color: #f9fafb; font-weight: bold; }
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

def create_word_document(content_text, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    doc.add_paragraph(f"Uczeń: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line: doc.add_paragraph(); continue
        if line.startswith('### '): doc.add_heading(line[4:], level=3)
        elif line.startswith('## '): doc.add_heading(line[3:], level=2)
        elif line.startswith('# '): doc.add_heading(line[2:], level=1)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(line[2:])
        else:
            doc.add_paragraph(line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFEJS ---
st.title("🎓 Asystent Pedagoga PRO v2")
st.markdown('<div class="men-badge">🏆 KLASA S: Inteligentne Szablony i Tabele</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    st.markdown("---")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

tab1, tab2 = st.tabs(["📁 1. Dane i Szablony", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("1. Wzór dokumentu (Twój Szablon)")
    template_file = st.file_uploader("Wgraj tutaj pusty wzór lub dokument z tabelą, który AI ma naśladować:", type=['pdf', 'docx'])
    
    st.markdown("---")
    st.subheader("2. Dane ucznia i diagnoza")
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
        diagnosis = st.text_area("❗ Główna diagnoza:", placeholder="Np. Spektrum autyzmu, afazja...", height=80)
    with c2:
        files = st.file_uploader("Wgraj orzeczenia PPP do analizy (DANE):", type=['pdf', 'docx'], accept_multiple_files=True)

    st.markdown("---")
    st.subheader("3. Szczegółowe zasoby i trudności")
    c3, c4 = st.columns(2)
    with c3:
        strengths = st.text_area("💪 Mocne strony i potencjał:", placeholder="W czym uczeń jest dobry?", height=100)
    with c4:
        weaknesses = st.text_area("🚧 Trudności i bariery:", placeholder="Z czym ma największy problem?", height=100)

    if st.button("⚙️ GENERUJ WEDŁUG SZABLONU"):
        if not is_pro:
            st.error("🔒 Odblokuj wersję PREMIUM kodem KAWA2024!")
        elif not s_name or not diagnosis:
            st.error("⚠️ Podaj przynajmniej imię i diagnozę!")
        else:
            with st.spinner("🚀 Analizuję szablon i piszę dokument..."):
                # Pobranie wzoru
                template_text = extract_text_from_file(template_file) if template_file else "Brak wzoru, użyj standardowej struktury IPET."
                
                # Pobranie danych z orzeczeń
                data_text = ""
                if files:
                    for f in files: data_text += f"\n--- PLIK DANYCH: {f.name} ---\n" + extract_text_from_file(f)
                
                sys_msg = f"""Jesteś ekspertem pedagogiki specjalnej. 
                TWOIM PRIORYTETEM JEST UKŁAD DOKUMENTU.
                SZABLON DO NAŚLADOWANIA:
                {template_text}
                
                ZASADY:
                1. Jeśli powyższy szablon zawiera tabele, odtwórz je w Markdown.
                2. Zachowaj wszystkie nagłówki i kolejność sekcji z szablonu.
                3. Wypełnij sekcje szablonu profesjonalną treścią na podstawie danych ucznia.
                4. Styl formalny. Zwróć TYLKO czysty tekst dokumentu."""

                usr_msg = f"""DANE UCZNIA: {s_name}
                DIAGNOZA: {diagnosis}
                MOCNE STRONY: {strengths}
                TRUDNOŚCI: {weaknesses}
                DANE Z ORZECZEŃ: {data_text[:10000]}"""

                try:
                    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                        "temperature": 0.3 # Niższa temperatura = większa dokładność w trzymaniu się szablonu
                    }
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
                    
                    if response.ok:
                        final_doc = response.json()["choices"][0]["message"]["content"]
                        st.session_state['generated_doc'] = final_doc
                        st.session_state['s_name'] = s_name
                        st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd'.")
                    else:
                        st.error("Błąd API. Sprawdź środki na koncie OpenAI.")
                except Exception as e:
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc = st.session_state['generated_doc']
        st.download_button("📁 POBIERZ WORD (.DOCX)", create_word_document(doc, st.session_state['s_name']), file_name=f"dokument_{st.session_state['s_name']}.docx", type="primary")
        st.markdown("---")
        html = markdown.markdown(doc, extensions=['tables'])
        st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else:
        st.info("Wypełnij dane i kliknij Generuj.")

st.markdown("---")
st.caption("EduBox AI © 2026 | Obsługa spersonalizowanych szablonów placówek")
