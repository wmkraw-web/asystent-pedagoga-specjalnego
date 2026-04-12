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
            # 1. Czytanie zwykłych akapitów
            for para in doc.paragraphs: 
                if para.text.strip(): text += para.text + "\n"
            # 2. Czytanie TABEL (Wcześniej AI ich nie widziało!)
            for table in doc.tables:
                text += "\n[TUTAJ ZACZYNA SIĘ TABELA DO WYPEŁNIENIA]\n"
                for row in table.rows:
                    row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                    text += "| " + " | ".join(row_data) + " |\n"
                text += "[KONIEC TABELI]\n\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e: st.error(f"Błąd odczytu pliku: {e}")
    return text

def _add_bold_parts(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- GENERATOR PLIKU WORD Z TABELAMI ---
def create_word_document(content_text, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    doc.add_paragraph(f"Uczeń: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    in_table = False
    table = None
    
    lines = content_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: 
            in_table = False
            doc.add_paragraph()
            continue
            
        # Detekcja i budowa tabeli Markdown w pliku Word
        if line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            
            # Ignorowanie wiersza oddzielającego nagłówki (np. |---|---|)
            if all(c.replace('-', '').replace(':', '').strip() == '' for c in cells):
                continue
                
            if not in_table:
                in_table = True
                # Tworzymy nową tabelę w Wordzie
                table = doc.add_table(rows=1, cols=len(cells))
                table.style = 'Table Grid'
                hdr_cells = table.rows[0].cells
                for i, cell_text in enumerate(cells):
                    if i < len(hdr_cells):
                        hdr_cells[i].text = ""
                        _add_bold_parts(hdr_cells[i].paragraphs[0], cell_text)
            else:
                # Dodajemy wiersz do istniejącej tabeli
                row_cells = table.add_row().cells
                for i, cell_text in enumerate(cells):
                    if i < len(row_cells):
                        row_cells[i].text = ""
                        _add_bold_parts(row_cells[i].paragraphs[0], cell_text)
            continue
        else:
            in_table = False
            
        # Generowanie zwykłych tekstów i nagłówków
        if line.startswith('### '): doc.add_heading(line[4:], level=3)
        elif line.startswith('## '): doc.add_heading(line[3:], level=2)
        elif line.startswith('# '): doc.add_heading(line[2:], level=1)
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

# --- INTERFEJS ---
st.title("🎓 Asystent Pedagoga PRO v2")
st.markdown('<div class="men-badge">🏆 KLASA S: Inteligentne Szablony i Rysowanie Tabel</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    st.markdown("---")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

tab1, tab2 = st.tabs(["📁 1. Dane i Szablony", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("1. Wzór dokumentu (Twój Szablon)")
    st.info("💡 Jeśli Twój szablon posiada tabele, koniecznie wgraj go w formacie **.DOCX (Word)**. AI idealnie rozpozna wtedy układ kolumn i wierszy!")
    template_file = st.file_uploader("Wgraj tutaj pusty wzór z tabelą, który AI ma naśladować (tylko DOCX lub PDF):", type=['pdf', 'docx'])
    
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
            with st.spinner("🚀 Analizuję układ tabel w Twoim szablonie i piszę dokument..."):
                template_text = extract_text_from_file(template_file) if template_file else "Brak wzoru, użyj standardowej struktury IPET w formie tabelarycznej."
                
                data_text = ""
                if files:
                    for f in files: data_text += f"\n--- PLIK DANYCH: {f.name} ---\n" + extract_text_from_file(f)
                
                sys_msg = f"""Jesteś wybitnym ekspertem pedagogiki specjalnej. 
                TWOIM BEZWZGLĘDNYM PRIORYTETEM JEST ZACHOWANIE STRUKTURY DOKUMENTU.
                
                SZABLON DO NAŚLADOWANIA:
                {template_text}
                
                ZASADY KRYTYCZNE:
                1. MUSISZ odtworzyć KARDĄ tabelę znajdującą się w szablonie, używając formatu Markdown (np. | Kolumna 1 | Kolumna 2 |). To Twój główny obowiązek.
                2. MUSISZ zachować i napisać wszystkie nagłówki z szablonu (używaj # dla tytułów, ## dla sekcji).
                3. Wypełnij wiersze tabeli oraz sekcje profesjonalną, konkretną treścią na podstawie danych ucznia.
                4. Zwróć TYLKO czysty dokument w formacie Markdown. Żadnych wstępów, żadnych uwag końcowych."""

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
                        "temperature": 0.2 
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
