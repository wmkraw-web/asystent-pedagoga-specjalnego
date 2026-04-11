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

# --- OSTATECZNY PARSER AI (ODPORNY NA BŁĘDY MODELI ROZUMUJĄCYCH) ---
def clean_ai_response(raw_text):
    raw_text = raw_text.strip()
    
    # Usunięcie bloków kodu, jeśli AI ubrało JSON w markdown
    if raw_text.startswith("```json"):
        raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
        
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

    # 2. Brutalne wyciąganie tekstu z zepsutego JSON-a (Zastępuje \n na nową linię)
    if '"content":"' in raw_text:
        # Szukamy początku prawdziwego tekstu
        start_idx = raw_text.find('"content":"') + 11
        content_str = raw_text[start_idx:]
        
        # Odcinamy końcówki systemowe, jeśli występują
        if '","tool_calls":' in content_str:
            content_str = content_str.split('","tool_calls":')[0]
        elif content_str.endswith('"}'):
            content_str = content_str[:-2]
            
        # Zamiana technicznych znaków ucieczki na prawdziwy tekst
        content_str = content_str.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
        return content_str.strip()

    # 3. Jeśli nie było JSON-a, wycinamy tagi <think>
    clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    return clean_text.strip()

# --- GENERATOR PLIKU WORD (.DOCX) ---
def create_word_document(content_text, doc_type, student_name):
    doc = docx.Document()
    
    # Główne formatowanie dokumentu
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    # Nagłówek
    heading = doc.add_heading(doc_type, level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Dotyczy ucznia: {student_name}").bold = True
    doc.add_paragraph("_" * 60)
    
    # Parsowanie prostego Markdowna z AI na format Worda
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue
            
        # Nagłówki
        if line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        # Listy punktowe
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_formatted_text(p, line[2:])
        # Zwykły tekst
        else:
            p = doc.add_paragraph()
            _add_formatted_text(p, line)
            
    # Zapis do bufora pamięci
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_formatted_text(paragraph, text):
    """Pomocnicza funkcja do pogrubiania tekstu między gwiazdkami **tekst**"""
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0:  # Co drugi element był wewnątrz gwiazdek
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

# --- INTERFEJS UŻYTKOWNIKA ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("🎓 Asystent Pedagoga PRO")
    st.markdown('<div class="men-badge">✓ Algorytm zgodny z wytycznymi MEN</div>', unsafe_allow_html=True)
    st.markdown("Wykorzystaj potęgę AI do analizy orzeczeń z Poradni Psychologiczno-Pedagogicznej i generuj kompletne dokumenty gotowe do wydruku.")
with col_head2:
    st.info("💡 **PRO TIP:** Wgraj skan diagnozy (PDF), a AI samo wyciągnie z niego wnioski do dokumentu!")

st.markdown("---")

# --- KONTROLA DOSTĘPU (PREMIUM) ---
with st.sidebar:
    st.header("🔒 Panel Kontrolny")
    access_code = st.text_input("Kod dostępu Premium:", type="password")
    is_premium = False
    if access_code.upper() == "KAWA2024":
        is_premium = True
        st.success("✅ Wersja PRO aktywna!")
    elif access_code:
        st.error("❌ Błędny kod!")
    
    st.markdown("---")
    st.warning("🛡️ **RODO:** Pamiętaj, aby przed wgraniem plików usunąć z nich dane wrażliwe (PESEL, dokładny adres). Używaj inicjałów!")
    st.markdown("[☕ Postaw Kawę Twórcy](https://buycoffee.to/magiccolor)")

# --- FORMULARZ GŁÓWNY ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📂 1. Dane i Dokumenty Bazowe")
    student_name = st.text_input("Imię / Inicjały ucznia:", placeholder="np. Jan K.")
    student_age = st.text_input("Klasa / Wiek:", placeholder="np. Klasa 2b / 8 lat")
    doc_type = st.selectbox("Wybierz rodzaj dokumentu do wygenerowania:", list(MEN_TEMPLATES.keys()))
    st.markdown("#### Wgraj orzeczenie lub opinię z PPP (Opcjonalnie)")
    uploaded_files = st.file_uploader("Dodaj pliki .PDF, .DOCX lub .TXT", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    
with col2:
    st.markdown("### 🎯 2. Wytyczne i Kontekst")
    diagnosis = st.text_input("Główna Diagnoza (jeśli nie wgrywasz pliku):", placeholder="np. Spektrum autyzmu, dysleksja, afazja...")
    context = st.text_area("Twoje własne obserwacje i zalecenia:", placeholder="Wpisz tutaj swoje notatki, np.\n- Uczeń szybko się rozprasza.\n- Potrzebuje częstych przerw ruchowych.", height=150)
    st.info(f"📚 **Sekcje obowiązkowe dla tego dokumentu:**\n{MEN_TEMPLATES[doc_type]}")

st.markdown("---")

# --- GENERATOR AI ---
if st.button("⚙️ GENERUJ DOKUMENT (Analiza AI)", type="primary"):
    
    if not uploaded_files and not diagnosis.strip() and not context.strip():
        st.error("⚠️ Podaj diagnozę, wgrać dokument lub wpisz obserwacje, aby AI miało na czym pracować!")
    else:
        with st.spinner("🤖 Analizuję dane i opracowuję profesjonalny dokument... To może zająć do 30 sekund."):
            
            extracted_text = ""
            if uploaded_files:
                for file in uploaded_files:
                    extracted_text += f"--- PLIK: {file.name} ---\n"
                    extracted_text += extract_text_from_file(file) + "\n\n"
            
            system_msg = f"""Jesteś wybitnym ekspertem pedagogiki specjalnej w Polsce. Twoim zadaniem jest opracowanie profesjonalnego dokumentu szkolnego ({doc_type}).
            Dokument musi być bezwzględnie zgodny z polskim prawem oświatowym.
            Ton musi być wysoce formalny, analityczny, pedagogiczny i obiektywny. 
            WYMOGI FORMALNE (Musisz uwzględnić te punkty jako nagłówki):
            {MEN_TEMPLATES[doc_type]}
            Zwróć TYLKO ostateczny dokument w formacie Markdown. NIE ZWRACAJ FORMATU JSON. Używaj nagłówków (#) oraz pogrubień (**)."""

            user_msg = f"""
            DANE UCZNIA: {student_name if student_name else 'N.N.'}, {student_age if student_age else 'wiek nieznany'}
            DIAGNOZA: {diagnosis if diagnosis else 'Zgodnie z załączonymi dokumentami'}
            
            WŁASNE OBSERWACJE NAUCZYCIELA: 
            {context if context else 'Brak dodatkowych obserwacji.'}
            
            WGRANE DOKUMENTY (Z ORZECZEŃ):
            {extracted_text if extracted_text else 'Brak wgranych plików.'}
            
            Zadanie: Napisz pełny i szczegółowy {doc_type}. Pomiń wszelkie wstępy, podsumowania i znaczniki JSON. Zwróć tylko czysty tekst dokumentu.
            """

            payload = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "model": "openai" 
            }

            try:
                response = requests.post("[https://text.pollinations.ai/](https://text.pollinations.ai/)", json=payload, timeout=60)
                
                if response.ok:
                    raw_result = response.text
                    final_doc = clean_ai_response(raw_result)
                    
                    st.success("✅ Analiza zakończona! Dokument został przygotowany.")
                    
                    # --- PREZENTACJA WYNIKÓW (MERCEDES) ---
                    st.markdown("### 📄 Twój Dokument")
                    
                    # POBIERANIE JAKO .DOCX (MS Word)
                    docx_buffer = create_word_document(final_doc, doc_type, student_name)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        st.download_button(
                            label="📥 POBIERZ JAKO PLIK WORD (.DOCX)",
                            data=docx_buffer,
                            file_name=f"{doc_type.split(' ')[0]}_{student_name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True
                        )
                    with col_btn2:
                        st.info("Pobierz plik Word, aby łatwo go wydrukować, dodać pieczątki i podpisy dyrekcji.")

                    # WIZUALNY PODGLĄD A4 (Koniec z surowym polem tekstowym)
                    st.markdown("#### Podgląd wydruku:")
                    st.markdown(f'<div class="a4-paper">{final_doc}</div>', unsafe_allow_html=True)
                    
                else:
                    st.error(f"Błąd połączenia z serwerem AI ({response.status_code}).")
            
            except requests.exceptions.Timeout:
                st.error("⏳ Serwer AI potrzebował zbyt dużo czasu na odpowiedź. Zmniejsz ilość wgranych plików.")
            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {str(e)}")

st.markdown("---")
st.caption("EduBox AI © 2026 | System do zautomatyzowanego wsparcia nauczycieli i pedagogów.")
