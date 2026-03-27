import streamlit as st
import json
import google.generativeai as genai

# --- 1. LOGOWANIE (SECRETS) ---
def setup_ai():
    if "google_credentials" in st.secrets:
        creds = json.loads(st.secrets["google_credentials"])
        # Wyciągamy klucz prywatny z JSONa
        api_key = creds.get("api_key") # Jeśli masz klucz API
        # Jeśli używasz Service Account (JSON), Vertex może blokować. 
        # Spróbujmy zainicjować przez API Key jeśli go masz, 
        # lub użyć credentials bezpośrednio:
        return creds
    return None

creds_dict = setup_ai()

# --- 2. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga", page_icon="📝")
st.title("📝 Asystent Dokumentacji Pedagogicznej")

# --- 3. WYBÓR I OPIS ---
typ = st.selectbox("Rodzaj dokumentu:", ["WOPFU", "IPET", "Ewaluacja", "Rewalidacja"])
opis = st.text_area("Dane ucznia (bez nazwisk):", height=200)

if st.button("✨ GENERUJ"):
    if not creds_dict:
        st.error("Brak klucza w Secrets!")
    else:
        try:
            # Próba połączenia nową metodą (Generative AI)
            # Jeśli w Twoim JSONie nie ma pola 'api_key', spróbujemy 
            # użyć projektu Vertex, ale z inną nazwą modelu.
            
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            vertexai.init(project=creds_dict["project_id"], location="us-central1")
            
            # TESTUJEMY RÓŻNE NAZWY - jedna z nich MUSI zadziałać:
            model_names = ["gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]
            
            success = False
            for name in model_names:
                try:
                    model = GenerativeModel(name)
                    response = model.generate_content(f"Napisz {typ} dla: {opis}")
                    st.markdown("### Wynik:")
                    st.write(response.text)
                    success = True
                    break
                except:
                    continue
            
            if not success:
                st.error("Google nadal nie udostępnia modelu. Sprawdź czy Vertex AI API jest włączone w konsoli.")
                
        except Exception as e:
            st.error(f"Błąd krytyczny: {e}")