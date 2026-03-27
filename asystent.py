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

# --- 2. FUNKCJA AI (MISTRAL AI) ---
def generate_mistral(prompt, context_files=""):
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza MISTRAL_API_KEY w Secrets!"
    
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    full_prompt = f"{prompt}\n\nKONTEKST Z PLIKÓW:\n{context_files}"
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem pedagogiki specjalnej. Tworzysz profesjonalną dokumentację (WOPFU, IPET, Ewaluacje) zgodnie z przepisami MEN. Jeśli używasz tabel, stosuj format: | Nagłówek 1 | Nagłówek 2 |."},
            {"role": "user", "content": full_prompt}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except:
        return "Błąd połączenia z silnikiem AI."

# --- 3. FUNKCJA GENEROWANIA PLIKU WORD ---
def create_word(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    
    lines = text.split('\n')
    table_data = []
    in_table = False
    
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith('|'):
            in_table = True
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if all(c.replace('-', '').replace(':', '') == '' for c in cells): continue
            if cells: table_data.append(cells)
        else:
            if in_table and table_data:
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                table.style = 'Table Grid'
                for i, row_data in enumerate(table_data):
                    for j, cell_text in enumerate(row_data):
                        if j < len(table.columns): table.cell(i, j).text = cell_text
                table_data = []
                in_table = False
            
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
st.set_page_config(page_title="Asystent Pedagoga PRO", page_icon="📝")
st.title("📝 Asystent Dokumentacji Pedagogicznej")

# Sidebar - Pliki
st.sidebar.header("📂 Załączniki")
files = st.sidebar.file_uploader("Wgraj dokumenty (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

# Formularz
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", ["WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", "Ewaluacja Półroczna", "Ewaluacja Końcoworoczna"])
with col2:
    etap = st.selectbox("Etap:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area("Opis bieżący ucznia:", height=150)

if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia and not files:
        st.warning("Dodaj opis lub wgraj pliki.")
    else:
        with st.spinner("AI analizuje dokumenty i pisze tekst..."):
            kontekst = ""
            for f in files:
                if f.name.endswith('.docx'): kontekst += read_docx(f)
                elif f.name.endswith('.pdf'): kontekst += read_pdf(f)
                else: kontekst += f.read().decode('utf-8')
            
            prompt_final = f"Napisz profesjonalny {typ_doc} dla ucznia ({etap}). Opis: {opis_ucznia}. Stosuj tabele dla celów i dostosowań."
            wynik = generate_mistral(prompt_final, kontekst)
            
            st.session_state['wynik'] = wynik
            st.session_state['nazwa_pliku'] = f"{typ_doc}_{etap}".replace(" ", "_")

if 'wynik' in st.session_state:
    st.markdown("### 📄 Projekt dokumentu:")
    st.markdown(st.session_state['wynik'])
    
    word_data = create_word(st.session_state['wynik'], st.session_state['nazwa_pliku'])
    st.download_button(label="📥 POBIERZ JAKO PLIK WORD (.docx)", data=word_data, file_name=f"{st.session_state['nazwa_pliku']}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# --- 5. STOPKA I KAWA ---
# --- 5. STOPKA I KAWA ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    st.markdown("### ☕ Podoba Ci się to narzędzie?")
    st.write("Utrzymanie serwerów AI kosztuje. Jeśli moja aplikacja zaoszczędziła Ci czas, możesz wesprzeć projekt.")
    
    # --- STYLOWY PRZYCISK BUYCOFFEE ---
    button_html = """
    <a href="https://buycoffee.to/TWOJA_NAZWA" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: #FFDD00;
            color: #000000;
            padding: 12px 24px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            font-weight: bold;
            font-family: sans-serif;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <img src="https://buycoffee.to/img/icons/coffee-icon.svg" style="width: 24px; margin-right: 10px;">
            Postaw mi kawę
        </div>
    </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)

with c2:
    with st.expander("⚖️ Regulamin i Prywatność"):
        st.write("1. Aplikacja nie przechowuje wgranych plików ani wpisanych danych.")
        st.write("2. Wygenerowany tekst jest jedynie projektem - ostateczna treść zależy od nauczyciela.")
        st.write("3. Korzystanie z aplikacji oznacza akceptację zasad dobrowolnego wsparcia projektu.")

st.caption("Asystent Pedagoga PRO v3.0 | 2026")