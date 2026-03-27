import streamlit as st
import requests
from docx import Document
from io import BytesIO

# --- 1. FUNKCJA GENEROWANIA (MISTRAL AI) ---
def generate_mistral(prompt, context_files=""):
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza MISTRAL_API_KEY w Secrets!"
    
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Łączymy prompt z dodatkowym kontekstem z plików
    full_prompt = f"{prompt}\n\nOto dodatkowe wytyczne/dokumenty do uwzględnienia:\n{context_files}"
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system", 
                "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację (WOPFU, IPET, Ewaluacja). Twoim zadaniem jest stworzyć dokument na podstawie opisu i załączonych wytycznych. Pisz merytorycznie, w punktach."
            },
            {"role": "user", "content": full_prompt}
        ]
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()['choices'][0]['message']['content']

# --- 2. FUNKCJA TWORZENIA PLIKU WORD ---
def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    # Proste formatowanie - dzielimy tekst na linie
    for line in text.split('\n'):
        doc.add_paragraph(line)
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. INTERFEJS ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")
st.title("📝 Asystent Dokumentacji PRO")
st.divider()

# Sekcja plików
st.sidebar.header("📂 Dodatkowe dokumenty")
file_dziecko = st.sidebar.file_uploader("Wgraj dokumenty dziecka (txt)", type=['txt'], help="Np. wypis z orzeczenia")
file_szkola = st.sidebar.file_uploader("Wgraj wytyczne szkoły/tabelę (txt)", type=['txt'], help="Np. wzór tabeli wymagań")

# Formularz główny
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", ["WOPFU", "IPET", "Rewalidacja", "Ewaluacja Półroczna"])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Opis sytuacji ucznia:", height=150)

# --- 4. LOGIKA ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia:
        st.warning("Wpisz opis dziecka.")
    else:
        with st.spinner("Analizuję pliki i generuję dokument..."):
            # Czytanie plików jeśli są wgrane
            kontekst = ""
            if file_dziecko:
                kontekst += f"\nDokument dziecka: {file_dziecko.read().decode('utf-8')}"
            if file_szkola:
                kontekst += f"\nWytyczne placówki: {file_szkola.read().decode('utf-8')}"
            
            prompt_final = f"Stwórz {typ_doc} dla etapu {etap}. Opis: {opis_ucznia}"
            wynik = generate_mistral(prompt_final, kontekst)
            
            # Zapisujemy wynik w sesji, żeby nie zniknął przy pobieraniu
            st.session_state['ostatni_wynik'] = wynik
            st.session_state['tytul'] = f"{typ_doc}_projekt"

if 'ostatni_wynik' in st.session_state:
    st.markdown("### 📄 Wygenerowany tekst:")
    st.markdown(st.session_state['ostatni_wynik'])
    
    # Przycisk pobierania WORD
    docx_file = create_word(st.session_state['ostatni_wynik'], st.session_state['tytul'])
    st.download_button(
        label="📥 POBIERZ JAKO PLIK WORD (.docx)",
        data=docx_file,
        file_name=f"{st.session_state['tytul']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

st.divider()
st.caption("MagicColor AI - Moduł Pedagogiczny v2.0")