import streamlit as st
import requests
from docx import Document
from io import BytesIO
import PyPDF2
from docx.shared import Pt, Inches

# --- 1. FUNKCJE CZYTANIA PLIKÓW ---
def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# --- 2. FUNKCJA AI (MISTRAL AI PRO) ---
def generate_mistral_pro(prompt, context_files=""):
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza MISTRAL_API_KEY w Secrets!"
    
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    full_prompt = f"{prompt}\n\nKONTEKST Z WGRANYCH PLIKÓW (UWZGLĘDNIJ TO):\n{context_files}"
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system", 
                "content": "Jesteś ekspertem pedagogiki specjalnej. Twoim zadaniem jest stworzyć profesjonalną, merytoryczną dokumentację (WOPFU, IPET, Ewaluacje) zgodnie z terminologią MEN. Pisz w punktach, stosuj czytelne tabele dla celów i dostosowań."
            },
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.5 # Niższa temperatura - bardziej konserwatywne, profesjonalne wyniki
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status() # Sprawdza błędy HTTP
        return response.json()['choices'][0]['message']['content']
    except:
        return "Coś poszło nie tak podczas generowania. Sprawdź, czy klucz API jest poprawny w Secrets."

# --- 3. FUNKCJA WORD PRO (TABELE I FORMATOWANIE) ---
def create_word_pro(text, title):
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    doc.add_heading(title, 0)
    
    lines = text.split('\n')
    table_data = []
    in_table = False
    
    for line in lines:
        clean_line = line.strip()
        
        # Wykrywanie tabeli
        if clean_line.startswith('|'):
            in_table = True
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue
            if cells:
                table_data.append(cells)
        else:
            # Rysowanie tabeli
            if in_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for i, row_data in enumerate(table_data):
                        for j, cell_text in enumerate(row_data):
                            if j < len(table.columns):
                                table.cell(i, j).text = cell_text
                except: pass
                table_data = []
                in_table = False
            
            # Dodawanie tekstu z czyszczeniem Markdown
            if clean_line:
                is_bold = clean_line.startswith('**') or clean_line.startswith('#')
                clean_text = clean_line.replace('**', '').replace('###', '').replace('##', '').replace('#', '').strip()
                p = doc.add_paragraph(clean_text)
                if is_bold:
                    p.bold = True
            else:
                doc.add_paragraph("")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. INTERFEJS UŻYTKOWNIKA PRO ---
# FINAL FAVICON DODANY TUTAJ
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="favicon.png")

# Nagłówek i Logo
col_logo, col_text = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo.png", width=100)
    except:
        pass # Ignoruje jeśli logo jeszcze nie wgrane
with col_text:
    st.title("Asystent Dokumentacji PRO")
    st.caption("🚀 *Inteligentne wsparcie w dokumentacji (Zgodny z MEN)*")
st.divider()

# Sidebar - Pliki
st.sidebar.header("📂 Dodatkowe dokumenty")
st.sidebar.info("Wgraj PDF, DOCX lub TXT (wytyczne placówki, orzeczenia).")
uploaded_files = st.sidebar.file_uploader("Dodaj załączniki", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

# Główne pola
col_left, col_right = st.columns(2)
with col_left:
    typ_doc = st.selectbox("Rodzaj dokumentu:", [
        "WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", 
        "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"
    ])
with col_right:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Bieżące informacje o uczniu (diagnoza, wyzwania):", height=150, placeholder="Opisz ucznia swoimi słowami, bez nazwiska...")

# --- 5. LOGIKA GENEROWANIA ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not uploaded_files:
        st.warning("Najpierw wpisz opis ucznia lub dodaj pliki.")
    else:
        with st.spinner("AI analizuje dokumenty i tworzy projekt..."):
            
            # Odczyt kontekstu z wielu plików
            kontekst = ""
            for f in uploaded_files:
                try:
                    if f.name.endswith('.docx'): kontekst += f"\n--- PLIK: {f.name} ---\n{read_docx(f)}"
                    elif f.name.endswith('.pdf'): kontekst += f"\n--- PLIK: {f.name} ---\n{read_pdf(f)}"
                    else: kontekst += f"\n--- PLIK: {f.name} ---\n{f.read().decode('utf-8')}"
                except:
                    st.error(f"Nie udało się odczytać pliku {f.name}.")
            
            prompt_final = f"""
            Napisz profesjonalny проект: {typ_doc} dla etapu: {etap}.
            Opis: {opis_ucznia}.
            WAŻNE: Przedstaw cele, metody i dostosowania w formie CZYTELNYCH TABEL Markdown. 
            Używaj języka merytorycznego. Zadbaj o anonimizację (uczeń: Jan K.).
            """
            
            wynik = generate_mistral_pro(prompt_final, kontekst)
            
            st.session_state['wynik'] = wynik
            st.session_state['tytul'] = f"{typ_doc}_{etap}".replace(" ", "_")

# Wyświetlanie wyniku
if 'wynik' in st.session_state:
    st.markdown("### 📄 Propozycja dokumentu:")
    st.markdown(st.session_state['wynik'])
    st.divider()
    
    # Przycisk pobierania Word
    word_data = create_word_pro(st.session_state['wynik'], st.session_state['tytul'])
    st.download_button(
        label="📥 POBIERZ JAKO PLIK WORD (.docx)",
        data=word_data,
        file_name=f"{st.session_state['tytul']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# --- 6. STOPKA, KAWA I FINALNY REGULAMIN ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.markdown("### ☕ Podoba Ci się to narzędzie?")
    st.write("Utrzymanie serwerów AI kosztuje. Jeśli moja aplikacja zaoszczędziła Ci czas, możesz wesprzeć projekt.")
    
    # --- PRZYCISK BUYCOFFEE PRO ---
    button_html = """
    <a href="https://buycoffee.to/magiccolor" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: #FFDD00;
            color: #000000;
            padding: 12px 24px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            font-weight: bold;
            font-family: sans-serif;
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <img src="https://buycoffee.to/img/icons/coffee-icon.svg" style="width: 24px; margin-right: 10px;">
            Postaw mi kawę
        </div>
    </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)

with c2:
    with st.expander("⚖️ Regulamin i Zasady Prawne"):
        st.write("""
        1. **Zgodność z przepisami:** Projekty dokumentów są generowane w oparciu o standardy merytoryczne i terminologię stosowaną w rozporządzeniach MEN dot. kształcenia specjalnego.
        2. **Charakter pomocniczy:** Aplikacja jest narzędziem wspomagającym. Wygenerowany tekst stanowi **projekt dokumentu**, który musi zostać zweryfikowany przez Zespół placówki. Twórca nie ponosi odpowiedzialności za ostateczną treść dokumentacji.
        3. **RODO:** Nie przechowujemy wgranych plików ani wpisanych opisów na serwerach po zakończeniu sesji.
        4. **Wsparcie:** Darowizny są dobrowolne i wspierają utrzymanie infrastruktury AI narzędzia.
        """)

st.caption("Asystent Pedagoga PRO v3.0 | 2026")