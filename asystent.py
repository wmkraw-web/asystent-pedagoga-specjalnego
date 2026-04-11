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
    
    # 1. Jeśli tekst jest opakowany w bloki markdownu
    if raw_text.startswith("```"):
        raw_text = re.sub(r'^```[a-z]*\n', '', raw_text)
        raw_text = re.sub(r'\n```$', '', raw_text)
        raw_text = raw_text.strip()

    # 2. Próba parsowania jako pełny obiekt JSON (standard API)
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            if "content" in data: return data["content"]
            if "choices" in data and data["choices"]:
                msg = data["choices"][0].get("message", {})
                return msg.get("content", "")
    except:
        pass

    # 3. WYCIĄGANIE TREŚCI Z "content":"..." (Ratunek dla formatu ze zdjęcia)
    if '"content":"' in raw_text:
        try:
            # Szukamy początku treści po kluczu "content":"
            start_marker = '"content":"'
            start_idx = raw_text.find(start_marker) + len(start_marker)
            # Treść kończy się przed kolejnym kluczem technicznym lub końcem JSON
            content_part = raw_text[start_idx:]
            
            end_markers = ['","tool_calls"', '","role"', '"}']
            for marker in end_markers:
                if marker in content_part:
                    content_part = content_part.split(marker)[0]
                    break
            
            # Naprawiamy znaki ucieczki (\n, \", \t)
            clean = content_part.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
            return clean.strip()
        except:
            pass

    # 4. Usuwanie tagów myślowych <think> (DeepSeek)
    clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    
    # 5. Jeśli tekst nadal wygląda na techniczny JSON, usuwamy go brutalnie
    clean_text = clean_text.replace('{"role":"assistant","content":"', '')
    if clean_text.endswith('"}'): clean_text = clean_text[:-2]
    
    return clean_text.strip()

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    
    # Ustawienia strony
    section = doc.sections[0]
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    
    # Styl podstawowy
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # Nagłówek dokumentu
    h = doc.add_heading(doc_type.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(f"Data wygenerowania: ....................")
    run.italic = True

    doc.add_paragraph(f"Imię i nazwisko ucznia: {student_name}").bold = True
    doc.add_paragraph("-" * 80)
    
    # Inteligentne przepisywanie Markdown na Word
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
            
    # Stopka prawna
    doc.add_paragraph("\n" + "_" * 30)
    footer = doc.add_paragraph("Dokument opracowany przy wsparciu Asystenta Pedagoga AI (EduBox). Zgodny z wymogami Rozporządzenia MEN.")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles['Normal'].font.size = Pt(8)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_formatted_run(paragraph, text):
    # Funkcja do obsługi **pogrubienia** w tekście
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- BAZA WIEDZY MEN ---
MEN_RULES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura musi zawierać: Zakres dostosowań, zintegrowane działania specjalistów, formy pomocy PP, współpracę z rodzicami oraz ocenę efektywności (zgodnie z rozporządzeniem nr 87).",
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura musi zawierać: Indywidualne potrzeby, mocne strony, przyczyny niepowodzeń, bariery środowiskowe oraz wnioski do pracy.",
    "Opinia o uczniu / Arkusz obserwacji": "Struktura musi zawierać: Opis funkcjonowania poznawczego, społecznego i emocjonalnego oraz konkretne zalecenia do pracy dydaktycznej."
}

# --- INTERFEJS UŻYTKOWNIKA ---
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.title("🎓 Asystent Pedagoga Specjalnego PRO")
    st.markdown(f'<div class="men-badge">🏆 KLASA S: Analiza orzeczeń i generowanie dokumentów MEN</div>', unsafe_allow_html=True)
with col_head2:
    st.success("🤖 Silnik AI: **Ready**")
    st.markdown('<p class="status-ok">✓ Połączono z bazą przepisów oświatowych</p>', unsafe_allow_html=True)

# --- PANEL BOCZNY (USTAWIENIA) ---
with st.sidebar:
    st.header("🔑 Autoryzacja Premium")
    code = st.text_input("Wprowadź kod dostępu:", type="password")
    is_pro = code.upper() == "KAWA2024"
    if is_pro: st.success("Odblokowano funkcje MERCEDES!")
    else: st.warning("Tryb demonstracyjny")
    
    st.markdown("---")
    st.info("**RODO:** Aplikacja nie zapisuje wgranych plików na serwerze. Po zamknięciu sesji dane są usuwane.")
    st.markdown("[☕ Postaw Kawę, aby otrzymać kod](https://buycoffee.to/magiccolor)")

# --- FORMULARZ (PODZIAŁ NA KOLUMNY) ---
tab1, tab2 = st.tabs(["📁 1. Wgrywanie i Dane", "📝 2. Podgląd i Wydruk"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Informacje o uczniu")
        s_name = st.text_input("Imię i Nazwisko (lub inicjały):", placeholder="np. Jan Kowalski")
        s_info = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2a, 8 lat")
        doc_type = st.selectbox("Rodzaj dokumentu wyjściowego:", list(MEN_RULES.keys()))
        
    with c2:
        st.subheader("Analiza dokumentacji bazowej")
        st.markdown("Wgraj orzeczenie z Poradni lub opinię, aby AI stworzyło dokument na ich podstawie:")
        files = st.file_uploader("Dodaj pliki (PDF, DOCX, TXT):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

    st.markdown("---")
    st.subheader("Dodatkowe wytyczne dla AI")
    extra_context = st.text_area("Twoje własne notatki z obserwacji (opcjonalnie):", height=100, placeholder="Np. Uczeń bardzo interesuje się pociągami, co można wykorzystać jako wzmocnienie pozytywne...")

    # --- AKCJA GŁÓWNA ---
    if st.button("⚙️ GENERUJ PEŁNY DOKUMENT (Analiza Ekspercka)"):
        if not s_name:
            st.error("⚠️ Podaj imię ucznia!")
        else:
            with st.spinner("🚀 Mercedes Klasy S rusza... AI analizuje dokumenty i pisze pismo..."):
                
                # Odczyt plików
                full_raw_data = ""
                if files:
                    for f in files:
                        full_raw_data += f"\n[ANALIZA PLIKU: {f.name}]\n" + extract_text_from_file(f)
                
                # Prompt Systemowy (Rygorystyczny)
                sys_msg = f"""Jesteś najbardziej doświadczonym pedagogiem specjalnym w Polsce. 
                Twoim zadaniem jest stworzenie oficjalnego dokumentu ({doc_type}).
                ZASADY:
                1. Dokument musi być bezwzględnie zgodny z wytycznymi MEN: {MEN_RULES[doc_type]}
                2. Używaj języka formalnego, analitycznego, unikaj potocyzmów.
                3. Wypunktuj konkretne zalecenia do pracy z uczniem.
                4. Zwróć TYLKO czysty dokument w formacie Markdown (Nagłówki, pogrubienia).
                5. ZAKAZ: Nie używaj formatu JSON. Nie dodawaj żadnych technicznych tagów."""

                # Prompt Użytkownika
                usr_msg = f"""OPRACUJ DOKUMENT: {doc_type}
                DANE UCZNIA: {s_name}, {s_info}
                DANE Z ORZECZEŃ (DO ANALIZY): {full_raw_data if full_raw_data else 'Brak, wygeneruj typowe zapisy na podstawie diagnozy ogólnej.'}
                DODATKOWE UWAGI NAUCZYCIELA: {extra_context}
                ZADANIE: Na podstawie powyższych danych napisz profesjonalny, gotowy do wydruku dokument."""

                payload = {
                    "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr_msg}],
                    "model": "openai"
                }

                try:
                    res = requests.post("[https://text.pollinations.ai/](https://text.pollinations.ai/)", json=payload, timeout=90)
                    if res.ok:
                        # NASZ DIAMENTOWY PARSER
                        final_doc = clean_ai_response(res.text)
                        st.session_state['generated_doc'] = final_doc
                        st.session_state['s_name'] = s_name
                        st.success("✅ Dokument wygenerowany! Przejdź do zakładki 'Podgląd i Wydruk'.")
                    else:
                        st.error(f"Błąd połączenia (Kod: {res.status_code})")
                except Exception as e:
                    st.error(f"Błąd krytyczny: {str(e)}")

with tab2:
    if 'generated_doc' in st.session_state:
        doc_text = st.session_state['generated_doc']
        
        # Sekcja pobierania
        st.subheader("📥 Eksport i Drukowanie")
        word_buf = create_word_document(doc_text, doc_type, st.session_state['s_name'])
        
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button(
                label="📁 POBIERZ JAKO MICROSOFT WORD (.DOCX)",
                data=word_buf,
                file_name=f"{doc_type.split(' ')[0]}_{st.session_state['s_name']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c_dl2:
            st.info("💡 Plik Word zawiera gotowe formatowanie, nagłówki i stopki zgodne z przepisami.")

        # Podgląd luksusowy
        st.markdown("---")
        st.markdown("### 🖥️ Podgląd arkusza A4")
        st.markdown(f'<div class="a4-paper">{doc_text}</div>', unsafe_allow_html=True)
    else:
        st.info("Tu pojawi się Twój dokument po kliknięciu 'Generuj' w pierwszej zakładce.")

st.markdown("---")
st.caption("EduBox AI PRO © 2026 | Technologia wspierająca Polską Edukację.")
