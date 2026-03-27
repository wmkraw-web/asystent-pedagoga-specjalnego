import streamlit as st
import requests
from docx import Document
from io import BytesIO
import PyPDF2
import os

# --- 1. FUNKCJE CZYTANIA PLIKÓW ---
def read_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except: return ""

def read_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages: text += page.extract_text()
        return text
    except: return ""

# --- 2. FUNKCJA AI (MISTRAL AI) ---
def generate_mistral_pro(prompt, context_files=""):
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza API w Secrets!"
    
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    full_prompt = f"{prompt}\n\nKONTEKST Z WGRANYCH PLIKÓW:\n{context_files}"
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację (WOPFU, IPET, Ewaluacje) zgodnie z terminologią MEN. Pisz merytorycznie, w punktach, stosuj czytelne tabele."},
            {"role": "user", "content": full_prompt}
        ]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except:
        return "Błąd połączenia z serwerem AI."

# --- 3. FUNKCJA WORD PRO ---
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
                    for i, row_data in enumerate(table_data):
                        for j, cell_text in enumerate(row_data):
                            if j < len(table.columns): table.cell(i, j).text = cell_text
                except: pass
                table_data, in_table = [], False
            
            if clean_line:
                is_bold = clean_line.startswith('**') or clean_line.startswith('#')
                clean_text = clean_line.replace('**', '').replace('#', '').strip()
                p = doc.add_paragraph(clean_text)
                if is_bold: p.bold = True
            else:
                doc.add_paragraph("")
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 4. INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="favicon.png", layout="wide")

with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    st.header("📂 Załączniki")
    uploaded_files = st.file_uploader("Dodaj PDF, DOCX lub TXT", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("Asystent Dokumentacji PRO")
    st.caption("🚀 Inteligentne wsparcie pedagoga (Zgodny z MEN)")

st.divider()

c1, c2 = st.columns(2)
with c1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", ["WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"])
with c2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Informacje o uczniu (bez nazwiska):", height=200, placeholder="Np. Janek, spektrum autyzmu...")

if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not uploaded_files:
        st.warning("Opisz ucznia lub dodaj pliki.")
    else:
        with st.spinner("Pracuję..."):
            kontekst = ""
            for f in uploaded_files:
                if f.name.endswith('.docx'): kontekst += read_docx(f)
                elif f.name.endswith('.pdf'): kontekst += read_pdf(f)
                else: kontekst += f.read().decode('utf-8')
            
            prompt = f"Napisz projekt {typ_doc} dla etapu {etap}. Dane: {opis_ucznia}. Stosuj tabele dla celów."
            wynik = generate_mistral_pro(prompt, kontekst)
            st.session_state['wynik'] = wynik
            st.session_state['nazwa'] = f"{typ_doc}_{etap}".replace(" ", "_")

if 'wynik' in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state['wynik'])
    data = create_word_pro(st.session_state['wynik'], "Projekt_Dokumentacji")
    st.download_button(label="📥 POBIERZ PLIK WORD", data=data, file_name=f"{st.session_state['nazwa']}.docx")

# --- 5. STOPKA I REGULAMIN Z NOWYM PRZYCISKIEM ---
st.divider()
bottom_c1, bottom_c2 = st.columns(2)
with bottom_c1:
    st.markdown("### ☕ Podoba Ci się to narzędzie?")
    # NOWY ZIELONY PRZYCISK Z TWOJEGO SCREENA
    kawa_code = """
    <a href="https://buycoffee.to/magiccolor" target="_blank">
        <img src="https://buycoffee.to/static/img/share/share-button-primary.png" style="width: 280px; height: auto;" alt="Postaw mi kawę na buycoffee.to">
    </a>
    """
    st.markdown(kawa_code, unsafe_allow_html=True)

with bottom_c2:
    with st.expander("⚖️ Regulamin i Zasady Prawne"):
        st.write("""
        1. **Zgodność z przepisami:** Projekty są generowane w oparciu o standardy merytoryczne i terminologię stosowaną w rozporządzeniach MEN dot. kształcenia specjalnego.
        2. **Charakter pomocniczy:** Aplikacja jest narzędziem wspomagającym. Wygenerowany tekst stanowi **projekt dokumentu**, który musi zostać zweryfikowany przez Zespół ds. pomocy psychologiczno-pedagogicznej w danej placówce.
        3. **Odpowiedzialność:** Twórca aplikacji nie ponosi odpowiedzialności za ostateczną treść dokumentacji oraz decyzje organów nadzorczych. Ostateczny kształt dokumentu musi być dostosowany do indywidualnych potrzeb ucznia.
        4. **Prywatność (RODO):** Narzędzie przetwarza dane w sposób ulotny. Nie przechowujemy wgranych plików ani opisów na serwerach po zakończeniu sesji.
        5. **Wsparcie:** Darowizny są dobrowolne i wspierają rozwój oraz utrzymanie infrastruktury technicznej narzędzia.
        """)

st.caption("Asystent Pedagoga PRO v3.0 | 2026")