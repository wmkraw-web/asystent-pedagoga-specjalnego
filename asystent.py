import streamlit as st
import requests
from docx import Document
from io import BytesIO
import PyPDF2
import os

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

# --- 2. SILNIK AI (MISTRAL) ---
def generate_mistral_pro(prompt, context_files=""):
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza API w Secrets!"
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    full_prompt = f"{prompt}\n\nKONTEKST Z PLIKÓW:\n{context_files}"
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację szkolną zgodnie z MEN. Pisz merytorycznie, w punktach, stosuj tabele."},
            {"role": "user", "content": full_prompt}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except: return "Błąd połączenia z serwerem AI."

# --- 3. KREATOR WORD ---
def create_word_pro(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    lines = text.split('\n')
    table_data, in_table = [], False
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith('|'):
            in_table = True
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if all(c.replace('-', '').replace(':', '') == '' for c in cells): continue
            if cells: table_data.append(cells)
        else:
            if in_table and table_data:
                try:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    for i, row in enumerate(table_data):
                        for j, val in enumerate(row):
                            if j < len(table.columns): table.cell(i, j).text = val
                except: pass
                table_data, in_table = [], False
            if clean_line:
                p = doc.add_paragraph(clean_line.replace('**', '').replace('#', '').strip())
                if line.strip().startswith('**') or line.strip().startswith('#'): p.bold = True
            else: doc.add_paragraph("")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")

# Boczny panel (Sidebar)
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    
    st.header("📂 Załączniki")
    uploaded_files = st.file_uploader("Dodaj PDF/DOCX", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    
    st.divider()
    
    # --- NOWA, STAŁA INSTRUKCJA (BEZ KLIKANIA) ---
    st.markdown("### 💡 Jak pisać opis?")
    st.info("""
    1. **Diagnoza:** Podaj główną przyczynę orzeczenia.
    2. **Mocne strony:** Opisuj, co uczeń potrafi.
    3. **Konkrety:** Podaj konkretne zachowania zamiast ogólników.
    4. **Zalecenia:** Wypisz 2-3 najważniejsze punkty z orzeczenia.
    """)

# Główna zawartość
st.title("Asystent Dokumentacji PRO")
st.caption("🚀 Inteligentne wsparcie pedagoga (Zgodny z MEN)")
st.divider()

col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", ["WOPFU", "IPET", "Rewalidacja", "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Informacje o uczniu (bez nazwiska):", height=200, placeholder="Np. Janek, spektrum autyzmu...")

if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not uploaded_files:
        st.warning("Opisz ucznia lub wgraj pliki.")
    else:
        with st.spinner("AI analizuje dane..."):
            kontekst = ""
            for f in uploaded_files:
                if f.name.endswith('.docx'): kontekst += read_docx(f)
                elif f.name.endswith('.pdf'): kontekst += read_pdf(f)
                else: kontekst += f.read().decode('utf-8')
            prompt = f"Stwórz profesjonalny projekt {typ_doc} dla etapu {etap}. Dane: {opis_ucznia}. Stosuj tabele dla celów."
            wynik = generate_mistral_pro(prompt, kontekst)
            st.session_state['wynik'] = wynik
            st.session_state['nazwa'] = f"{typ_doc}_{etap}".replace(" ", "_")

if 'wynik' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['wynik'])
    data = create_word_pro(st.session_state['wynik'], "Projekt_Dokumentacji")
    st.download_button(label="📥 POBIERZ PLIK WORD", data=data, file_name=f"{st.session_state['nazwa']}.docx")

# --- 5. STOPKA I KAWA ---
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.markdown("### ☕ Podoba Ci się narzędzie?")
    # ZMIEŃ LINK PONIŻEJ NA SWÓJ:
    st.markdown('<a href="https://buycoffee.to/magiccolor" target="_blank" style="text-decoration: none;"><div style="background-color: #FFDD00; color: #000; padding: 12px; border-radius: 12px; text-align: center; font-weight: bold;">Postaw mi kawę</div></a>', unsafe_allow_html=True)
with c2:
    st.markdown("**Regulamin i RODO**")
    st.caption("Dane są przetwarzane tylko na czas generowania dokumentu. Ostateczna treść dokumentu należy do nauczyciela.")

st.caption("Asystent Pedagoga PRO v3.0 | 2026")