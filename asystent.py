import streamlit as st
import requests
from docx import Document
from io import BytesIO
import PyPDF2
import os

# --- FUNKCJE POMOCNICZE ---
def read_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages: text += page.extract_text()
    return text

def generate_mistral_pro(prompt, context_files=""):
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz dokumentację MEN w tabelach."},
            {"role": "user", "content": f"{prompt}\n\nKontekst: {context_files}"}
        ]
    }
    res = requests.post(url, json=data, headers=headers)
    return res.json()['choices'][0]['message']['content']

def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    for line in text.split('\n'):
        doc.add_paragraph(line.replace('**', '').replace('#', '').strip())
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- INTERFEJS BEZ SIDEBARA (WSZYSTKO NA ŚRODKU) ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")

if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

st.title("Asystent Dokumentacji PRO")
st.divider()

# INSTRUKCJA NA WIERZCHU
st.info("""
### 💡 Jak pisać opis?
1. **Diagnoza:** Podaj przyczynę orzeczenia.
2. **Mocne strony:** Co uczeń potrafi?
3. **Konkrety:** Opisuj zachowania, nie ogólniki.
""")

st.divider()

# PLIKI I FORMULARZ
st.subheader("1. Dodaj dokumenty i opis")
uploaded_files = st.file_uploader("Wgraj PDF/DOCX (opcjonalnie)", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Dokument:", ["WOPFU", "IPET", "Rewalidacja", "Ewaluacja"])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Opis ucznia:", height=200)

if st.button("✨ GENERUJ PROJEKT"):
    with st.spinner("Pracuję..."):
        kontekst = ""
        for f in uploaded_files:
            if f.name.endswith('.docx'): kontekst += read_docx(f)
            elif f.name.endswith('.pdf'): kontekst += read_pdf(f)
            else: kontekst += f.read().decode('utf-8')
        
        prompt = f"Napisz projekt {typ_doc} dla etapu {etap}. Opis: {opis_ucznia}."
        wynik = generate_mistral_pro(prompt, kontekst)
        st.session_state['wynik'] = wynik

if 'wynik' in st.session_state:
    st.markdown("### 📄 Wynik:")
    st.markdown(st.session_state['wynik'])
    data = create_word(st.session_state['wynik'], "Dokument")
    st.download_button("📥 POBIERZ WORD", data=data, file_name="projekt.docx")

st.divider()
st.markdown("[☕ Postaw mi kawę](https://buycoffee.to/magiccolor)")
st.caption("v3.0 | Dane RODO nie są zapisywane.")