import streamlit as st
import requests
import json
import re

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="centered")

# --- NAGŁÓWEK ---
st.title("🎓 Asystent Pedagoga Specjalnego")
st.markdown("Wygeneruj profesjonalny szkic dokumentu szkolnego (IPET, WOPFU, Opinia) w kilkanaście sekund. Oszczędź swój czas!")

# --- KONTROLA DOSTĘPU (PREMIUM) ---
st.sidebar.header("🔒 Wersja PRO")
access_code = st.sidebar.text_input("Podaj kod Premium:", type="password")

is_premium = False
if access_code.upper() == "KAWA2024":
    is_premium = True
    st.sidebar.success("Kod poprawny! Odblokowano pełną moc Asystenta. 🎉")
elif access_code:
    st.sidebar.error("Nieprawidłowy kod. Postaw kawę autorowi, aby odblokować!")
    
st.sidebar.markdown("---")
st.sidebar.markdown("[☕ Postaw Kawę, aby wesprzeć serwery!](https://buycoffee.to/magiccolor)")

# --- FORMULARZ DANYCH ---
st.markdown("### 📝 Dane ucznia i diagnoza")

doc_type = st.selectbox("Wybierz rodzaj dokumentu:", [
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)", 
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)", 
    "Opinia Pedagogiczna / Psychologiczna"
])

col1, col2 = st.columns(2)
with col1:
    student_name = st.text_input("Imię (lub inicjały) ucznia:", placeholder="np. Jan K.")
with col2:
    student_age = st.text_input("Wiek / Klasa:", placeholder="np. 7 lat, 2 klasa")

diagnosis = st.text_input("Diagnoza / Powód objęcia wsparciem:", placeholder="np. Autyzm, afazja, trudności z matematyką...")
strengths = st.text_area("Mocne strony i zasoby (opcjonalnie):", placeholder="W czym uczeń jest dobry? Co lubi?")
difficulties = st.text_area("Trudności i bariery (opcjonalnie):", placeholder="Z czym ma największy problem na lekcjach?")

# --- GENEROWANIE ---
if st.button("✨ Generuj dokument (AI)", type="primary", use_container_width=True):
    if not diagnosis.strip():
        st.warning("Podaj chociaż diagnozę lub powód wsparcia, aby AI wiedziało, o czym pisać!")
    else:
        with st.spinner("Sztuczna Inteligencja analizuje dane i pisze dokument... To zajmie kilkanaście sekund. ⏳"):
            
            system_prompt = "Jesteś profesjonalnym polskim pedagogiem specjalnym. Twoim zadaniem jest napisanie oficjalnego, formalnego dokumentu szkolnego (np. IPET, WOPFU). Używaj języka specjalistycznego, obiektywnego i zgodnego z wytycznymi polskiego MEN. Użyj formatowania Markdown, wyraźnych nagłówków i list punktowych. Zwróć TYLKO czysty, ostateczny dokument po polsku. Żadnych wstępów, żadnych własnych przemyśleń w tekście."
            
            user_prompt = f"""
            Proszę o przygotowanie dokumentu: {doc_type}
            Dane ucznia:
            - Imię/Inicjały: {student_name if student_name else 'Uczeń'}
            - Wiek/Klasa: {student_age if student_age else 'brak danych'}
            - Diagnoza główna: {diagnosis}
            - Mocne strony i zasoby: {strengths if strengths else 'Wygeneruj ogólne, typowe dla tej diagnozy i wieku.'}
            - Trudności i bariery: {difficulties if difficulties else 'Wygeneruj ogólne, typowe dla tej diagnozy i wieku.'}
            """
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            try:
                # Strzał do serwera AI (np. Pollinations)
                response = requests.post("https://text.pollinations.ai/", json=payload, timeout=40)
                raw_text = response.text
                
                # ==========================================
                # PANCERNY PARSER AI (NAPRAWA BŁĘDU BIAŁEGO EKRANU I JSON)
                # ==========================================
                final_document = raw_text # Wartość domyślna
                
                # 1. Próba odczytania, czy serwer wysłał surowy słownik JSON (np. {"content": "...", "reasoning": "..."})
                try:
                    data = json.loads(raw_text)
                    if isinstance(data, dict):
                        if "choices" in data and len(data["choices"]) > 0:
                            final_document = data["choices"][0]["message"].get("content", raw_text)
                        elif "content" in data:
                            final_document = data["content"]
                    elif isinstance(data, list) and len(data) > 0 and "content" in data[0]:
                        final_document = data[0]["content"]
                except json.JSONDecodeError:
                    # To nie był JSON, to po prostu czysty tekst - zostawiamy.
                    pass
                
                # 2. Usunięcie tagów myślowych "DeepSeek" (<think> ... </think>), jeśli serwer je dodał w czystym tekście
                final_document = re.sub(r'<think>.*?</think>', '', final_document, flags=re.DOTALL)
                
                # 3. Oczyszczenie z pustych znaków
                final_document = final_document.strip()

                # --- SUKCES I WYŚWIETLENIE ---
                st.success(f"Sukces! Twój dokument **{doc_type}** został wygenerowany.")
                
                st.markdown("### 📄 Twój Dokument:")
                st.markdown("*(Poniższy tekst możesz dowolnie edytować przed skopiowaniem)*")
                
                # Wyświetlamy jako pole tekstowe do edycji, a nie surowy tekst
                st.text_area("Gotowy tekst (Zaznacz wszystko Ctrl+A i skopiuj Ctrl+C):", value=final_document, height=600)
                
                # Pobieranie jako plik tekstowy
                st.download_button(
                    label="📥 Pobierz jako plik tekstowy (.txt)",
                    data=final_document,
                    file_name=f"{doc_type[:4]}_{student_name}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error("Wystąpił błąd podczas łączenia z serwerem AI. Serwery mogą być przeciążone. Odczekaj chwilę i spróbuj ponownie.")
                st.error(f"Szczegóły błędu: {e}")

st.markdown("---")
st.caption("Pamiętaj: Wygenerowane dokumenty to wersje robocze, stworzone przez Sztuczną Inteligencję. Przed wydrukowaniem powinieneś je przeczytać i dostosować do faktycznego stanu ucznia, zgodnie ze swoją pedagogiczną wiedzą.")
