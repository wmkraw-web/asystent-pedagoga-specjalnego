import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURACJA AI ---
# Pobieramy klucz z Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Brakuje klucza GEMINI_API_KEY w Secrets!")

# --- 2. WYGLĄD APLIKACJI ---
st.set_page_config(page_title="Asystent Pedagoga", page_icon="📝")
st.title("📝 Asystent Dokumentacji Pedagogicznej")
st.markdown("---")

# --- 3. INPUT UŻYTKOWNIKA ---
typ_doc = st.selectbox("Rodzaj dokumentu:", [
    "WOPFU", "IPET", "Rewalidacja", "Ewaluacja Półroczna"
])

opis_ucznia = st.text_area("Opisz diagnozę i potrzeby ucznia (bez nazwisk):", height=200)

if st.button("✨ GENERUJ PROJEKT"):
    if not opis_ucznia:
        st.warning("Najpierw opisz ucznia!")
    else:
        with st.spinner("Generuję dokument..."):
            try:
                # Używamy modelu Flash 1.5 - jest najszybszy i najmniej problemowy
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                Jesteś ekspertem pedagogiki specjalnej. 
                Napisz profesjonalny projekt dokumentu: {typ_doc}.
                Na podstawie opisu: {opis_ucznia}.
                Używaj języka merytorycznego, terminologii pedagogicznej i formatowania w punktach.
                """
                
                response = model.generate_content(prompt)
                
                st.markdown("### 📄 Wygenerowany projekt:")
                st.write(response.text)
                st.success("Gotowe! Możesz teraz skopiować tekst.")
                
            except Exception as e:
                st.error(f"Coś poszło nie tak: {e}")

st.markdown("---")
st.caption("Aplikacja wspierająca pracę nauczyciela.")