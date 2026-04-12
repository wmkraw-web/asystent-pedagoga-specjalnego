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

# --- STYLE CSS (LUKSUSOWY INTERFEJS + BLUR DLA PAYWALLA) ---
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
    /* STYLIZACJA TABEL NA PODGLĄDZIE */
    .a4-paper table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
    .a4-paper th, .a4-paper td { border: 1px solid #cbd5e1; padding: 12px; text-align: left; }
    .a4-paper th { background-color: #f8fafc; font-weight: bold; }
    
    /* STYLE DLA WZORU POKAZOWEGO (PAYWALL) */
    .demo-watermark {
        background-color: #fff1f2;
        border: 2px dashed #f43f5e;
        color: #e11d48;
        padding: 15px;
        text-align: center;
        border-radius: 10px;
        font-weight: bold;
        margin: 20px 0;
    }
    .blurred-text {
        color: transparent;
        text-shadow: 0 0 8px rgba(0,0,0,0.4);
        user-select: none;
    }
    .status-ok { color: #059669; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJA NAPRAWIAJĄCA TABELE AI ---
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

# --- FUNKCJE POMOCNICZE (ODCZYT PLIKÓW I TABEL DOCX) ---
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
            for table in doc.tables:
                text += "\n[TABELA]\n"
                for row in table.rows:
                    row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                    text += "| " + " | ".join(row_data) + " |\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.getvalue().decode("utf-8")
    except Exception as e: st.error(f"Błąd odczytu pliku: {e}")
    return text

# --- GENERATOR PLIKU WORD (.DOCX) Z TABELAMI ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    
    h = doc.add_heading(doc_type.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Uczeń: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    in_table = False
    table_obj = None
    content_text = fix_markdown_tables(content_text)
    
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            in_table = False
            doc.add_paragraph()
            continue
            
        if line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if all(c.replace('-', '').replace(':', '').strip() == '' for c in cells):
                continue
            
            if not in_table:
                in_table = True
                table_obj = doc.add_table(rows=1, cols=len(cells))
                table_obj.style = 'Table Grid'
                row = table_obj.rows[0]
                for i, val in enumerate(cells):
                    p = row.cells[i].paragraphs[0]
                    _add_bold_parts(p, val)
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                row_cells = table_obj.add_row().cells
                for i, val in enumerate(cells):
                    if i < len(row_cells):
                        _add_bold_parts(row_cells[i].paragraphs[0], val)
            continue
        
        in_table = False
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

def _add_bold_parts(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- BAZA WIEDZY MEN I WZÓR POKAZOWY ---
MEN_RULES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura musi zawierać: Zakres dostosowań, zintegrowane działania specjalistów, formy pomocy PP, współpracę z rodzicami oraz ocenę efektywności.",
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura musi zawierać: Indywidualne potrzeby, mocne strony, przyczyny niepowodzeń, bariery środowiskowe oraz wnioski do pracy.",
    "Opinia o uczniu / Arkusz obserwacji": "Struktura musi zawierać: Opis funkcjonowania poznawczego, społecznego i emocjonalnego oraz zalecenia.",
    "Własny Dokument / Inny (Zgodnie z szablonem placówki)": "Wygeneruj dokument ściśle według szablonu podanego przez użytkownika."
}

DEMO_DOCUMENT = """
# INDYWIDUALNY PROGRAM EDUKACYJNO-TERAPEUTYCZNY (IPET)
**Uczeń:** Jan K. (Przykład)
**Klasa:** 2a

## 1. Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia (WOPFU) - Podsumowanie
Uczeń wykazuje bardzo dobre zdolności w zakresie logicznego myślenia oraz zapamiętywania ciągów liczbowych. Główne trudności obserwuje się w obszarze integracji sensorycznej oraz nawiązywania relacji rówieśniczych w grupie (spektrum autyzmu).

## 2. Zakres i sposób dostosowania wymagań edukacyjnych
- Wydłużenie czasu na sprawdzianach o 50%.
- Dzielenie dłuższych poleceń na krótsze, proste komunikaty.
- Zapewnienie wyciszonego miejsca pracy, z dala od bodźców rozpraszających.
- <span class='blurred-text'>Dostosowanie formy sprawdzania wiedzy do możliwości psychofizycznych ucznia. Zamiast odpowiedzi ustnych, preferowane odpowiedzi pisemne lub testy wyboru.</span>

## 3. Zintegrowane działania nauczycieli i specjalistów
- Udział w Treningu Umiejętności Społecznych (TUS) - 1 godzina w tygodniu.
- <span class='blurred-text'>Stała współpraca wychowawcy z psychologiem szkolnym w celu monitorowania nastroju i zachowań agresywnych podczas przerw. Konsultacje z logopedą raz w miesiącu.</span>

<div class='demo-watermark'>
    🔒 DALSZA CZĘŚĆ DOKUMENTU ZABLOKOWANA<br/>
    <span style='font-size:12px; font-weight:normal;'>To jest tylko statyczny wzór. Aby Sztuczna Inteligencja przeanalizowała TWOJE dane, wgrała tabele i napisała pełny, spersonalizowany dokument, odblokuj aplikację Kodem Premium!</span>
</div>
"""

# --- INTERFEJS ---
st.title("🎓 Asystent Pedagoga PRO v2")
st.markdown('<div class="men-badge">🏆 KLASA S: Inteligentne Tabele i Formaty Placówek</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔑 Autoryzacja")
    code = st.text_input("Kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje PREMIUM")
    else: st.warning("Tryb demonstracyjny (Wymagany Kod)")
    st.markdown("---")
    st.info("RODO: Używaj inicjałów ucznia!")
    st.markdown("[☕ Postaw Kawę](https://buycoffee.to/magiccolor)")

tab1, tab2 = st.tabs(["📁 1. Dane i Szablony", "📝 2. Podgląd i Wydruk"])

with tab1:
    st.subheader("1. Wybierz dokument lub wgraj własny szablon")
    st.info("💡 Chcesz, żeby AI wypełniło tabelkę Twojej szkoły? Wgraj wzór w formacie **.DOCX**!")
    
    c_doc1, c_doc2 = st.columns(2)
    with c_doc1:
        doc_type = st.selectbox("Wybierz rodzaj dokumentu:", list(MEN_RULES.keys()))
    with c_doc2:
        template_file = st.file_uploader("Opcjonalnie: Wgraj własny wzór (.DOCX):", type=['pdf', 'docx'])
    
    st.markdown("---")
    st.subheader("2. Dane ucznia i diagnoza")
    c1, c2 = st.columns(2)
    with c1:
        s_name = st.text_input("Imię / Inicjały ucznia:", placeholder="np. Jan K.")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a")
        diagnosis = st.text_area("❗ Główna diagnoza / opis problemu:", placeholder="Np. Spektrum autyzmu, afazja, ADHD...", height=100)
    with c2:
        files = st.file_uploader("Wgraj orzeczenia PPP (DANE):", type=['pdf', 'docx'], accept_multiple_files=True)

    st.markdown("---")
    st.subheader("3. Własne uwagi i cechy ucznia")
    c3, c4 = st.columns(2)
    with c3:
        strengths = st.text_area("💪 Mocne strony / Zasoby:", placeholder="W czym uczeń jest dobry?", height=120)
    with c4:
        weaknesses = st.text_area("🚧 Trudności / Bariery:", placeholder="Z czym ma największy problem?", height=120)

    if st.button("⚙️ GENERUJ DOKUMENT"):
        # --- ZABEZPIECZENIE (PAYWALL) ---
        if not is_pro:
            st.session_state['generated_doc'] = "DEMO_MODE"
            st.session_state['s_name'] = "Wzór Dokumentu"
            st.session_state['doc_type'] = "IPET (Wzór)"
            st.error("🔒 Odmowa dostępu: Aby wygenerować pełny dokument i wypełniać szablony tabel, wesprzyj projekt wirtualną kawą i wpisz Kod Premium w panelu po lewej stronie!")
            st.info("👉 Przejdź do zakładki 'Podgląd i Wydruk', aby zobaczyć PRZYKŁADOWY WZÓR dokumentu.")
        elif not OPENAI_API_KEY:
            st.error("⚠️ Brak skonfigurowanego klucza OpenAI w Streamlit Secrets!")
        elif not s_name or not diagnosis:
            st.error("⚠️ Podaj przynajmniej imię i diagnozę główną ucznia!")
        else:
            with st.spinner("🚀 Weryfikuję dane, analizuję szablony i piszę dokument..."):
                template_text = extract_text_from_file(template_file) if template_file else ""
                
                data_text = ""
                if files:
                    for f in files: data_text += f"\n--- PLIK DANYCH: {f.name} ---\n" + extract_text_from_file(f)
                
                if template_text:
                    template_instruction = f"Użytkownik wgrał WŁASNY SZABLON dokumentu. Twoim priorytetem jest zastosowanie tego układu oraz wszystkich tabel, które się w nim znajdują:\n{template_text}"
                else:
                    template_instruction = f"WYMAGANIA DLA TEGO DOKUMENTU: {MEN_RULES[doc_type]}"

                sys_msg = f"""Jesteś wybitnym ekspertem pedagogiki specjalnej. 
                TWOIM ZADANIEM JEST NAPISANIE LUB WYPEŁNIENIE DOKUMENTU: {doc_type}.
                
                ZASADY KRYTYCZNE:
                1. {template_instruction}
                2. Jeśli w układzie jest JAKAKOLWIEK TABELA, MUSISZ ją odtworzyć w standardzie Markdown (separator |---| jest obowiązkowy!).
                3. Zachowaj odpowiednie nagłówki.
                4. Zwróć tylko czysty dokument w Markdown. Żadnych wstępów ani komentarzy."""

                usr_msg = f"""DANE UCZNIA: {s_name}, {s_info}.
                DIAGNOZA GŁÓWNA: {diagnosis}.
                ZASOBY (Mocne strony): {strengths}.
                BARIERY (Trudności): {weaknesses}.
                ANALIZA ORZECZEŃ I DANYCH: {data_text[:12000]}"""

                try:
                    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                        "temperature": 0.25
                    }
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
                    
                    if response.ok:
                        raw_doc = response.json()["choices"][0]["message"]["content"]
                        st.session_state['generated_doc'] = fix_markdown_tables(raw_doc)
                        st.session_state['s_name'] = s_name
                        st.session_state['doc_type'] = doc_type
                        st.success("✅ Gotowe! Sprawdź zakładkę 'Podgląd i Wydruk'.")
                    else:
                        st.error("Błąd API OpenAI. Sprawdź środki na koncie.")
                except Exception as e:
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc = st.session_state['generated_doc']
        
        # --- TRYB POKAZOWY ---
        if doc == "DEMO_MODE":
            st.warning("👀 Tryb Pokazowy. Poniżej znajduje się przykładowy dokument. Odblokuj pełen dostęp kodem KAWA2024, aby pobrać i generować własne dokumenty z tabelami!")
            st.markdown("---")
            st.markdown(f"<div class='a4-paper'>{DEMO_DOCUMENT}</div>", unsafe_allow_html=True)
            
        # --- TRYB PEŁNY (PRO) ---
        else:
            st.subheader("📥 Eksport i Drukowanie")
            c_dl1, c_dl2 = st.columns(2)
            with c_dl1:
                word_buf = create_word_document(doc, st.session_state.get('doc_type', 'Dokument'), st.session_state['s_name'])
                st.download_button("📁 POBIERZ PLIK WORD (.DOCX)", word_buf, file_name=f"dokument_{st.session_state['s_name']}.docx", type="primary", use_container_width=True)
            with c_dl2:
                st.info("💡 AI zbudowało obramowane tabele. Zobaczysz je po pobraniu pliku Word!")

            st.markdown("---")
            st.markdown("### 🖥️ Podgląd arkusza A4")
            html = markdown.markdown(doc, extensions=['tables'])
            st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
    else:
        st.info("Wypełnij dane w zakładce obok i kliknij 'Generuj'.")

st.markdown("---")
st.caption("EduBox AI © 2026 | Płatny model API OpenAI (GPT-4o-mini)")
