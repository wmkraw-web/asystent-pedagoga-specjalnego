import streamlit as st
import requests
import json
import re
import io

# --- PRÓBA IMPORTU BIBLIOTEK DO ODCZYTU PLIKÓW ---
try:
    import PyPDF2
except ImportError:
    st.error("Brak biblioteki PyPDF2. Dodaj 'PyPDF2' do pliku requirements.txt")
try:
    import docx
except ImportError:
    st.error("Brak biblioteki python-docx. Dodaj 'python-docx' do pliku requirements.txt")

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: 800; font-size: 16px; transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .stTextArea textarea { border-radius: 12px; }
    .men-badge { background-color: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; padding: 8px 12px; border-radius: 8px; font-weight: bold; font-size: 12px; text-transform: uppercase; margin-bottom: 20px; display: inline-block;}
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

# --- PANCERNY PARSER AI (MÓZG) ---
def clean_ai_response(raw_text):
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                content = msg.get("content", "")
                if not content: 
                    content = data["choices"][0].get("text", "")
                return content
            elif "content" in data:
                return data["content"]
            elif "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", raw_text)
    except:
        pass

    content_match = re.search(r'"content":\s*"(.*?)"', raw_text, re.DOTALL)
    if content_match:
        content = content_match.group(1)
        try:
            return content.encode().decode('unicode_escape')
        except:
            return content

    processed = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    return processed.strip()

# --- SZABLONY WYMOGÓW MEN ---
MEN_TEMPLATES = {
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": """
        Dokument musi zawierać następujące sekcje zgodnie z MEN:
        1. Zakres i sposób dostosowania wymagań edukacyjnych.
        2. Zintegrowane działania nauczycieli i specjalistów.
        3. Formy i okres udzielania pomocy psychologiczno-pedagogicznej.
        4. Działania wspierające rodziców ucznia.
        5. Ocenę efektywności programu.
    """,
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": """
        Dokument musi zawierać następujące sekcje zgodnie z MEN:
        1. Indywidualne potrzeby rozwojowe i edukacyjne oraz możliwości psychofizyczne.
        2. Mocne strony, predyspozycje, zainteresowania i uzdolnienia.
        3. Przyczyny niepowodzeń edukacyjnych lub trudności w funkcjonowaniu.
        4. Bariery i ograniczenia utrudniające funkcjonowanie ucznia.
        5. Wnioski do dalszej pracy.
    """,
    "Opinia o uczniu / Arkusz obserwacji": """
        Dokument musi mieć formę profesjonalnej opinii pedagogicznej:
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
    st.markdown("Wykorzystaj potęgę AI do analizy orzeczeń z Poradni Psychologiczno-Pedagogicznej i generuj gotowe dokumenty w ułamku sekundy.")
with col_head2:
    st.info("💡 **PRO TIP:** Wgraj skan diagnozy lub orzeczenia (PDF), a AI samo wyciągnie z niego wnioski!")

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
    st.warning("🛡️ **RODO:** Pamiętaj, aby przed wgraniem plików usunąć z nich dokładne dane wrażliwe (PESEL, nazwisko, dokładny adres). Używaj inicjałów!")
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
    
    context = st.text_area("Twoje własne obserwacje i zalecenia:", 
                           placeholder="Wpisz tutaj swoje notatki, np.\n- Uczeń szybko się rozprasza.\n- Bardzo dobrze radzi sobie z matematyką.\n- Potrzebuje częstych przerw ruchowych.", 
                           height=150)
    
    st.info(f"📚 **Wymogi MEN dla wybranego dokumentu:**\n{MEN_TEMPLATES[doc_type]}")

st.markdown("---")

# --- GENERATOR AI ---
if st.button("⚙️ GENERUJ DOKUMENT (Analiza AI)", type="primary"):
    
    # Zabezpieczenie danych wejściowych
    if not uploaded_files and not diagnosis.strip() and not context.strip():
        st.error("⚠️ Musisz podać diagnozę, wgrać dokument lub wpisać własne obserwacje, aby AI miało na czym pracować!")
    else:
        with st.spinner("🤖 Analizuję wgrane dokumenty i układam strukturę według wymogów MEN... To może zająć do 30 sekund."):
            
            # Odczytywanie wgranych plików
            extracted_text = ""
            if uploaded_files:
                for file in uploaded_files:
                    extracted_text += f"--- PLIK: {file.name} ---\n"
                    extracted_text += extract_text_from_file(file) + "\n\n"
            
            # Budowanie Promptu Systemowego
            system_msg = f"""Jesteś wybitnym ekspertem pedagogiki specjalnej w Polsce. Twoim zadaniem jest opracowanie profesjonalnego dokumentu szkolnego ({doc_type}).
            Dokument musi być bezwzględnie zgodny z polskim prawem oświatowym i wytycznymi MEN. 
            Ton musi być formalny, analityczny, pedagogiczny i obiektywny.
            Nie używaj ogólników – opieraj się na dostarczonych materiałach. 
            WYMOGI FORMALNE:
            {MEN_TEMPLATES[doc_type]}
            Zwróć TYLKO ostateczny dokument w formacie Markdown. Nie dodawaj żadnych powitań, komentarzy ani podsumowań od siebie."""

            # Budowanie Promptu Użytkownika
            user_msg = f"""
            PRZYGOTUJ DOKUMENT: {doc_type}
            DANE UCZNIA: {student_name if student_name else 'Uczeń'}, {student_age if student_age else 'wiek nieznany'}
            DIAGNOZA: {diagnosis if diagnosis else 'Wynika z załączonych dokumentów'}
            
            WŁASNE OBSERWACJE NAUCZYCIELA: 
            {context if context else 'Brak dodatkowych obserwacji.'}
            
            TEKST Z WGRANYCH ORZECZEŃ/OPINII (do analizy):
            {extracted_text if extracted_text else 'Nie wgrano plików. Opieraj się na diagnozie i wytycznych MEN.'}
            
            Zadanie: Przeanalizuj powyższe dane, wyciągnij najważniejsze zalecenia terapeutyczne i stwórz profesjonalny, szczegółowy {doc_type}.
            """

            payload = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "model": "openai" # Stabilny model dla długich tekstów
            }

            try:
                response = requests.post("https://text.pollinations.ai/", json=payload, timeout=60)
                
                if response.ok:
                    raw_result = response.text
                    # Nasz niezawodny parser wyciągający tylko dokument
                    final_doc = clean_ai_response(raw_result)
                    
                    # Deska ratunku, jeśli parser nic nie złapał
                    if not final_doc or final_doc == raw_result:
                        final_doc = raw_result.replace('{"role":"assistant","content":"', '').replace('"}', '')

                    st.success("✅ Analiza zakończona! Dokument został wygenerowany zgodnie z wytycznymi MEN.")
                    
                    st.markdown("### 📄 Wynikowy Dokument")
                    st.markdown("*(Poniższy tekst możesz dowolnie edytować przed skopiowaniem lub pobraniem)*")
                    edited_text = st.text_area("Edytor dokumentu:", value=final_doc, height=600, label_visibility="collapsed")
                    
                    # Pobieranie
                    col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 2])
                    with col_dl1:
                        st.download_button(
                            "📥 Pobierz plik .TXT",
                            data=edited_text,
                            file_name=f"{doc_type[:4]}_{student_name}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col_dl2:
                         st.info("Kopiuj (Ctrl+C) i wklej do Worda (Ctrl+V)")
                else:
                    st.error(f"Błąd połączenia z serwerem AI ({response.status_code}). Spróbuj ponownie.")
            
            except requests.exceptions.Timeout:
                st.error("⏳ Serwer AI potrzebował zbyt dużo czasu na odpowiedź. Spróbuj wygenerować dokument podając mniej wgranych plików.")
            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {str(e)}")

st.markdown("---")
st.caption("EduBox AI © 2026 | Dokumenty wygenerowane przez sztuczną inteligencję mają charakter poglądowy i powinny zostać zweryfikowane przez specjalistę.")
