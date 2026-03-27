import streamlit as st
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# --- 1. LOGOWANIE DO GOOGLE ---
def get_creds():
    if "google_credentials" in st.secrets:
        creds_dict = json.loads(st.secrets["google_credentials"])
        return service_account.Credentials.from_service_account_info(creds_dict)
    return None

creds = get_creds()
PROJECT_ID = "decoded-reducer-449618-i7" # Twój ID projektu

if creds:
    vertexai.init(project=PROJECT_ID, location="us-central1", credentials=creds)

# --- 2. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga Specjalnego", page_icon="📝")

st.title("📝 Asystent Dokumentacji Pedagogicznej")
st.write("Profesjonalne wsparcie w tworzeniu WOPFU, IPET i Ewaluacji")

# --- 3. WYBÓR DOKUMENTU ---
typ_dokumentu = st.selectbox("Wybierz rodzaj dokumentu:", [
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)",
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)",
    "Program Zajęć Rewalidacyjnych",
    "Ewaluacja Półroczna/Roczna",
    "Ocena Efektywności Pomocy Psychologiczno-Pedagogicznej"
])

# --- 4. FORMULARZ DANYCH ---
st.info("⚠️ Pamiętaj o RODO! Zamiast nazwiska używaj inicjałów lub imienia (np. Jaś K.).")

opis_ucznia = st.text_area("Opisz diagnozę, mocne strony i deficyty ucznia:", height=200)

uploaded_file = st.file_uploader("Opcjonalnie: Wgraj tabelę wymagań lub wytyczne Twojej szkoły (plik tekstowy):", type=['txt'])

# --- 5. GENEROWANIE ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia:
        st.warning("Opisz ucznia, aby AI mogło stworzyć dokument.")
    else:
        with st.spinner("Analizuję przepisy i przygotowuję dokument..."):
            try:
                # Dodatkowe wytyczne z pliku
                dodatkowe_info = ""
                if uploaded_file:
                    dodatkowe_info = "\nUwzględnij te wytyczne z placówki: " + uploaded_file.read().decode("utf-8")

                # Profesjonalny "System Prompt" dla pedagoga
                instrukcja = f"""
                Jesteś doświadczonym pedagogiem specjalnym i ekspertem od przepisów MEN. 
                Twoim zadaniem jest napisać profesjonalny projekt dokumentu: {typ_dokumentu}.
                Używaj języka fachowego, opieraj się na terminologii pedagogicznej.
                Dane ucznia: {opis_ucznia}
                {dodatkowe_info}
                Dokument musi zawierać: cele, metody pracy, dostosowania wymagań i wnioski.
                Zadbaj o strukturę punktową, aby łatwo było ją skopiować do arkusza szkoły.
                """

                model = GenerativeModel("gemini-2.0-flash-exp")
                response = model.generate_content(instrukcja)
                
                st.markdown("### 📄 Propozycja dokumentu:")
                st.write(response.text)
                st.success("Gotowe! Możesz skopiować tekst do Worda.")

            except Exception as e:
                st.error(f"Błąd: {e}")

# Stopka
st.divider()
st.caption("Narzędzie wspierające - ostateczna treść dokumentu należy do nauczyciela prowadzącego.")