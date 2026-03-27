import streamlit as st
import requests
from docx import Document
from io import BytesIO
import PyPDF2

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
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    full_prompt = f"{prompt}\n\nKONTEKST Z PLIKÓW:\n{context_files}"
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację (WOPFU, IPET, Ewaluacje) zgodnie z przepisami MEN."},
            {"role": "user", "content": full_prompt}
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()['choices'][0]['message']['content']

# --- 3. FUNKCJA WORD ---
def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    for line in text.split('\n'):
        doc.add_paragraph(line)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. INTERFEJS ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")
st.title("📝 Asystent Dokumentacji PRO")

# Sidebar - Pliki
st.sidebar.header("📂 Załączniki (PDF, DOCX, TXT)")
files = st.sidebar.file_uploader("Wgraj dokumenty (orzeczenia, wytyczne)", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

# Formularz
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", [
        "WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", 
        "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"
    ])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Opis bieżący ucznia:", height=150)

# Główna logika
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not files:
        st.warning("Dodaj opis lub wgraj pliki.")
    else:
        with st.spinner("AI analizuje dokumenty i pisze tekst..."):
            # Odczyt kontekstu z wielu plików
            kontekst = ""
            for f in files:
                if f.name.endswith('.docx'): kontekst += read_docx(f)
                elif f.name.endswith('.pdf'): kontekst += read_pdf(f)
                else: kontekst += f.read().decode('utf-8')
            
            prompt_final = f"Napisz profesjonalny {typ_doc} dla ucznia ({etap}). Opis: {opis_ucznia}"
            wynik = generate_mistral(prompt_final, kontekst)
            
            # Zapis do session_state (zapobiega znikaniu przycisku)
            st.session_state['wynik'] = wynik
            st.session_state['nazwa_pliku'] = f"{typ_doc}_{etap}".replace(" ", "_")

# Wyświetlanie wyniku i przycisku pobierania
if 'wynik' in st.session_state:
    st.markdown("### 📄 Wygenerowany projekt:")
    st.info("Poniższy tekst możesz edytować po pobraniu pliku Word.")
    st.markdown(st.session_state['wynik'])
    
    word_data = create_word(st.session_state['wynik'], st.session_state['nazwa_pliku'])
    
    st.download_button(
        label="📥 POBIERZ JAKO PLIK WORD (.docx)",
        data=word_data,
        file_name=f"{st.session_state['nazwa_pliku']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

st.divider()
st.caption("Asystent v2.5 - Obsługa PDF/DOCX | Mistral AI")