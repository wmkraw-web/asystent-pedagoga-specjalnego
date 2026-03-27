import streamlit as st
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

# --- 1. LOGOWANIE DO GOOGLE ---
def get_creds():
    if "google_credentials" in st.secrets:
        creds_dict = json.loads(st.secrets["google_credentials"])
        return service_account.Credentials.from_service_account_info(creds_dict)
    return None

creds = get_creds()
PROJECT_ID = "decoded-reducer-449618-i7"

if creds:
    vertexai.init(project=PROJECT_ID, location="us-central1", credentials=creds)

# --- 2. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga", page_icon="📝")
st.title("📝 Asystent Dokumentacji Pedagogicznej")

# --- 3. WYBÓR I OPIS ---
typ_dokumentu = st.selectbox("Wybierz rodzaj dokumentu:", [
    "WOPFU", "IPET", "Program Zajęć Rewalidacyjnych", "Ewaluacja Półroczna/Roczna"
])

opis_ucznia = st.text_area("Opisz diagnozę i sytuację ucznia (bez nazwisk):", height=200)

if st.button("✨ GENERUJ DOKUMENT"):
    if not opis_ucznia:
        st.warning("Opisz ucznia przed generowaniem.")
    elif not creds:
        st.error("Błąd kluczy w Secrets!")
    else:
        with st.spinner("Pracuję nad dokumentem przy użyciu Gemini 2.0..."):
            try:
                # Używamy modelu 2.0, który widziałeś w konsoli
                model = GenerativeModel("gemini-2.0-flash-exp")
                
                instrukcja = f"""
                Jesteś ekspertem pedagogiki specjalnej. Napisz profesjonalny projekt: {typ_dokumentu}.
                Opis ucznia: {opis_ucznia}. 
                Używaj terminologii zgodnej z rozporządzeniami MEN. 
                Pisz konkretnie, merytorycznie, w punktach.
                """
                
                response = model.generate_content(instrukcja)
                
                st.markdown("### 📄 Projekt dokumentu:")
                st.write(response.text)
                st.success("Sukces! Możesz skopiować tekst.")
                
            except Exception as e:
                # Jeśli wersja exp nie zadziała, spróbujmy tej
                try:
                    model = GenerativeModel("gemini-2.0-flash-001")
                    response = model.generate_content(instrukcja)
                    st.write(response.text)
                except:
                    st.error(f"Błąd modelu: {e}")

# --- 4. STOPKA ---
st.divider()
st.caption("Aplikacja wykorzystuje model Gemini 2.0 Flash.")