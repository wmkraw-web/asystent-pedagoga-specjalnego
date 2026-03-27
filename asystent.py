import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURACJA AI ---
def setup_genai():
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return True
    return False

# --- 2. WYGLĄD I STYL ---
st.set_page_config(page_title="Asystent Pedagoga Specjalnego", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4A90E2; color: white; font-weight: bold; }
    .success-text { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 Asystent Dokumentacji")
st.subheader("WOPFU, IPET, Rewalidacja i Ewaluacja")
st.divider()

# --- 3. INPUT UŻYTKOWNIKA ---
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", [
        "WOPFU", 
        "IPET", 
        "Program Zajęć Rewalidacyjnych", 
        "Ewaluacja Półroczna/Roczna",
        "Ocena Efektywności Pomocy P-P"
    ])

with col2:
    etap = st.selectbox("Etap edukacyjny:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area(
    "Opisz ucznia (diagnoza, mocne strony, wyzwania):", 
    placeholder="Np. Jaś, lat 6, spektrum autyzmu. Dobrze radzi sobie z zadaniami wizualnymi, ma trudności z komunikacją społeczną...",
    height=200
)

# --- 4. LOGIKA GENEROWANIA ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not setup_genai():
        st.error("Błąd: Brak GEMINI_API_KEY w Secrets!")
    elif not opis_ucznia:
        st.warning("Proszę wpisać opis ucznia.")
    else:
        with st.spinner("Mózg AI pracuje nad dokumentacją..."):
            try:
                # Próbujemy różnych nazw modeli, by uniknąć błędu 404
                model_names = ['gemini-1.5-flash', 'gemini-pro']
                response_text = ""
                
                prompt = f"""
                Jesteś ekspertem pedagogiki specjalnej. Napisz profesjonalny, merytoryczny projekt dokumentu: {typ_doc}.
                Etap: {etap}.
                Opis ucznia: {opis_ucznia}.
                Używaj języka profesjonalnego (terminologia MEN). Dokument ma być w punktach, czytelny.
                Zaproponuj: cele terapeutyczne, formy pomocy, dostosowania wymagań oraz metody pracy.
                """

                model_found = False
                for m_name in model_names:
                    try:
                        model = genai.GenerativeModel(m_name)
                        response = model.generate_content(prompt)
                        response_text = response.text
                        model_found = True
                        break
                    except:
                        continue
                
                if model_found:
                    st.markdown("### 📄 Propozycja dokumentu:")
                    st.markdown(response_text)
                    st.success("Wygenerowano pomyślnie! Schowaj flaszkę, czas na kawę! ☕")
                    
                    # Przygotowanie do kopiowania
                    st.info("💡 Skopiuj powyższy tekst i wklej do swojego arkusza szkolnego.")
                else:
                    st.error("Google odrzuciło połączenie. Sprawdź czy klucz API jest aktywny w AI Studio.")

            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {e}")

# --- 5. STOPKA ---
st.divider()
st.caption("Aplikacja wspierająca - ostateczna treść dokumentu należy do nauczyciela. Zadbaj o RODO.")