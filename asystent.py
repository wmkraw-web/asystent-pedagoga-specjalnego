import streamlit as st
import requests

# --- 1. FUNKCJA GENEROWANIA (MISTRAL AI) ---
def generate_mistral(prompt):
    # Pobieramy klucz z Secrets
    if "MISTRAL_API_KEY" not in st.secrets:
        return "BŁĄD: Brak klucza MISTRAL_API_KEY w Secrets!"
    
    api_key = st.secrets["MISTRAL_API_KEY"]
    url = "https://api.mistral.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system", 
                "content": "Jesteś doświadczonym pedagogiem specjalnym. Tworzysz profesjonalną dokumentację szkolną (WOPFU, IPET, Ewaluacja) zgodnie z wytycznymi MEN. Pisz merytorycznie, w punktach, używając języka specjalistycznego."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status() # Sprawdza czy nie ma błędów HTTP
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Wystąpił błąd podczas łączenia z AI: {str(e)}"

# --- 2. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga Specjalnego", page_icon="📝")

st.title("📝 Asystent Dokumentacji Pedagogicznej")
st.markdown("🚀 *Wersja stabilna (Silnik Mistral AI)*")
st.divider()

# --- 3. FORMULARZ ---
col1, col2 = st.columns(2)
with col1:
    typ_doc = st.selectbox("Rodzaj dokumentu:", [
        "WOPFU", 
        "IPET", 
        "Program Zajęć Rewalidacyjnych", 
        "Ewaluacja Półroczna/Roczna"
    ])
with col2:
    etap = st.selectbox("Etap edukacyjny:", ["Przedszkole", "Szkoła Podstawowa", "Szkoła Ponadpodstawowa"])

opis_ucznia = st.text_area(
    "Opisz ucznia (diagnoza, trudności, mocne strony):", 
    placeholder="Np. Kasia, 8 lat, niepełnosprawność intelektualna w stopniu lekkim, trudności z koncentracją...",
    height=200
)

# --- 4. GENEROWANIE ---
if st.button("✨ GENERUJ PROJEKT DOKUMENTU"):
    if not opis_ucznia:
        st.warning("Proszę wpisać opis ucznia przed kliknięciem przycisku.")
    else:
        with st.spinner("Trwa analizowanie danych i pisanie dokumentu..."):
            
            prompt_final = f"Napisz projekt dokumentu {typ_doc} dla ucznia na etapie: {etap}. Dane do analizy: {opis_ucznia}"
            
            wynik = generate_mistral(prompt_final)
            
            st.markdown("### 📄 Propozycja dokumentu:")
            st.markdown(wynik)
            st.divider()
            st.success("Sukces! Możesz skopiować tekst do Worda.")

# --- 5. STOPKA ---
st.caption("Aplikacja wspierająca nauczyciela. Pamiętaj o zachowaniu zasad RODO.")