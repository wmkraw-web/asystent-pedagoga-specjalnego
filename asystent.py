import streamlit as st
import requests
from docx import Document
from docx.shared import Pt
from io import BytesIO
import PyPDF2
import re

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

# --- 2. FUNKCJA AI (MISTRAL) ---
def generate_mistral(prompt, context_files=""):
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
                "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację (WOPFU, IPET, Ewaluacje). Twoim zadaniem jest stworzyć dokument na podstawie opisu i załączonych wytycznych. Pisz merytorycznie, w punktach. Jeśli używasz tabel, stosuj format: | Nagłówek 1 | Nagłówek 2 |."
            },
            {"role": "user", "content": full_prompt}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()['choices'][0]['message']['content']

# --- 3. INTELIGENTNA FUNKCJA TWORZENIA WORD (TABELE I FORMATOWANIE) ---
def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    
    lines = text.split('\n')
    table_data = []
    in_table = False
    
    for line in lines:
        clean_line = line.strip()
        
        # Wykrywanie tabeli Markdown
        if clean_line.startswith('|'):
            in_table = True
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            # Ignorowanie separatorów |---|
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue
            if cells:
                table_data.append(cells)
        else:
            # Rysowanie tabeli w Wordzie jeśli dane się skończyły
            if in_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for i, row_data in enumerate(table_data):
                        for j, cell_text in enumerate(row_data):
                            if j < len(table.columns):
                                table.cell(i, j).text = cell_text
                except:
                    pass # Zabezpieczenie przed błędnym formatem tabeli
                table_data = []
                in_table = False
            
            # Dodawanie zwykłego tekstu
            if clean_line:
                # Czyszczenie Markdown (** i #)
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

# --- 4. INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")
st.title("📝 Asystent Dokumentacji Pedagogicznej")

# Sidebar - Pliki
st.sidebar.header("📂 Załączniki")
st.sidebar.info("Wgraj orzeczenie dziecka lub wzór tabeli szkoły.")
uploaded_files = st.sidebar.file_uploader("Dodaj PDF, DOCX lub TXT", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

# Główne pola
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", [
        "WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", 
        "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"
    ])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Bieżące informacje o uczniu:", height=150, placeholder="Np. Jan Kowalski, spektrum autyzmu, trudności w relacjach...")

# --- 5. LOGIKA GENEROWANIA ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not uploaded_files:
        st.warning("Proszę wpisać opis lub wgrać dokumenty.")
    else:
        with st.spinner("AI analizuje dane i tworzy tabele..."):
            # Czytanie plików
            kontekst = ""
            for f in uploaded_files:
                try:
                    if f.name.endswith('.docx'): kontekst += f"\n--- PLIK {f.name} ---\n{read_docx(f)}"
                    elif f.name.endswith('.pdf'): kontekst += f"\n--- PLIK {f.name} ---\n{read_pdf(f)}"
                    else: kontekst += f"\n--- PLIK {f.name} ---\n{f.read().decode('utf-8')}"
                except Exception as e:
                    st.error(f"Nie udało się odczytać pliku {f.name}: {e}")
            
            prompt_final = f"""
            Napisz profesjonalny projekt: {typ_doc} dla etapu: {etap}.
            Opis główny: {opis_ucznia}
            WAŻNE: Przedstaw cele, metody i dostosowania w formie CZYTELNYCH TABEL Markdown. 
            Usuń zbędne komentarze, skup się na merytoryce pedagogicznej.
            """
            
            wynik = generate_mistral(prompt_final, kontekst)
            st.session_state['wynik'] = wynik
            st.session_state['tytul'] = f"{typ_doc}_{etap}".replace(" ", "_")

# Wyświetlanie wyniku
if 'wynik' in st.session_state:
    st.markdown("### 📄 Podgląd projektu:")
    st.markdown(st.session_state['wynik'])
    
    # Przycisk pobierania Word
    word_data = create_word(st.session_state['wynik'], st.session_state['tytul'])
    
    st.download_button(
        label="📥 POBIERZ JAKO PLIK WORD (.docx)",
        data=word_data,
        file_name=f"{st.session_state['tytul']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

st.divider()
s# --- 6. STOPKA, KAWA I REGULAMIN ---
st.divider()
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Podoba Ci się to narzędzie?")
    st.write("Utrzymanie serwerów AI kosztuje. Jeśli moja aplikacja zaoszczędziła Ci czas, możesz wesprzeć projekt stawiając mi symboliczną kawę.")
    # Tutaj wklej swój link do BuyCoffee lub Typefury
    st.markdown("[☕ Postaw mi kawę na buycoffee.to](https://buycoffee.to/TWOJA_NAZWA)")

with col_right:
    with st.expander("⚖️ Informacje i Prywatność"):
        st.write("""
        1. **RODO:** Aplikacja nie przechowuje danych wpisanych w formularzu ani treści wgranych plików. Dane są przesyłane do AI w celu wygenerowania dokumentu i natychmiast usuwane.
        2. **Odpowiedzialność:** Wygenerowany tekst jest projektem pomocniczym. Ostateczną odpowiedzialność za treść dokumentacji ponosi nauczyciel.
        3. **Wsparcie:** Darowizny są dobrowolne i przeznaczone na pokrycie kosztów infrastruktury AI.
        """)

st.caption("Asystent Pedagoga PRO v3.0 | 2026")