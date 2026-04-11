iimport streamlit as st
import requests
import json
import re

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga AI - EduBox", page_icon="🎓", layout="centered")

# --- STYLE CSS DLA LEPSZEGO WYGLĄDU ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; }
    .stTextArea textarea { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- NAGŁÓWEK ---
st.title("🎓 Asystent Pedagoga Specjalnego")
st.markdown("Generuj profesjonalne dokumenty (IPET, WOPFU, Opinie) z pomocą AI. Oszczędź czas na biurokracji!")

# --- KONTROLA DOSTĘPU (PREMIUM) ---
st.sidebar.header("🔒 Panel Kontrolny")
access_code = st.sidebar.text_input("Kod dostępu Premium:", type="password")

is_premium = False
if access_code.upper() == "KAWA2024":
    is_premium = True
    st.sidebar.success("✅ Kod poprawny! Funkcje PRO aktywne.")
elif access_code:
    st.sidebar.error("❌ Błędny kod!")

st.sidebar.markdown("---")
st.sidebar.info("Ten asystent pomaga w tworzeniu szkiców dokumentacji. Zawsze zweryfikuj wynik z aktualnymi przepisami prawa oświatowego.")

# --- FORMULARZ DANYCH ---
st.markdown("### 📝 Dane do dokumentu")

doc_type = st.selectbox("Rodzaj dokumentu:", [
    "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)", 
    "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)", 
    "Opinia o uczniu / Arkusz obserwacji"
])

col1, col2 = st.columns(2)
with col1:
    student_name = st.text_input("Imię / Inicjały:", placeholder="np. Jan K.")
with col2:
    student_age = st.text_input("Wiek / Klasa:", placeholder="np. 8 lat, klasa 2")

diagnosis = st.text_input("Główna diagnoza / Trudności:", placeholder="np. spektrum autyzmu, dysleksja...")
context = st.text_area("Dodatkowe informacje (opcjonalnie):", placeholder="Wypisz od myślników mocne strony, bariery lub zalecenia z orzeczenia...", height=100)

# --- FUNKCJA PARSUJĄCA (MÓZG SYSTEMU) ---
def clean_ai_response(raw_text):
    """
    Ekstremalnie odporna funkcja wyciągająca czysty tekst z odpowiedzi AI.
    Obsługuje: JSON, Tagi <think>, reasoning_content.
    """
    try:
        # 1. Sprawdź czy to JSON (Pollinations/OpenAI API format)
        data = json.loads(raw_text)
        
        # Próba wyciągnięcia z różnych struktur JSON
        if isinstance(data, dict):
            # Standard OpenAI / DeepSeek API
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                content = msg.get("content", "")
                if not content: # Czasami tekst jest w 'text' (legacy)
                    content = data["choices"][0].get("text", "")
                return content
            # Bezpośredni format 'content'
            elif "content" in data:
                return data["content"]
            # Inne formaty słownikowe
            elif "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", raw_text)
    except:
        # Jeśli to nie JSON, działamy na surowym tekście
        pass

    # 2. Jeśli JSON zawiódł, użyj Regex, aby wyciągnąć pole "content" z tekstu, który WYGLĄDA jak JSON
    # To ratuje sytuację, gdy serwer wyśle błędny/ucięty JSON
    content_match = re.search(r'"content":\s*"(.*?)"', raw_text, re.DOTALL)
    if content_match:
        content = content_match.group(1)
        # Naprawiamy znaki ucieczki (\n, \" itp)
        return content.encode().decode('unicode_escape')

    # 3. Usuwanie tagów <think>...</think> (DeepSeek reasoning)
    processed = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    
    return processed.strip()

# --- GENEROWANIE ---
if st.button("✨ Generuj Dokument", type="primary"):
    if not diagnosis.strip():
        st.warning("⚠️ Wpisz diagnozę, aby AI wiedziało na czym się skupić.")
    else:
        with st.spinner("🤖 AI pracuje nad dokumentem... Proszę czekać."):
            
            system_msg = "Jesteś ekspertem pedagogiki specjalnej w Polsce. Tworzysz profesjonalną dokumentację szkolną (IPET, WOPFU) zgodnie z rozporządzeniami MEN. Używaj języka formalnego, specjalistycznego. Zwracaj WYŁĄCZNIE czysty dokument w formacie Markdown z nagłówkami. Nie dodawaj wstępów typu 'Oto Twój dokument'."
            
            user_msg = f"""Przygotuj dokument: {doc_type}. 
            Uczeń: {student_name if student_name else 'N.N.'}, {student_age if student_age else 'wiek nieznany'}.
            Diagnoza: {diagnosis}.
            Dodatkowe dane: {context if context else 'Brak, wygeneruj typowe zapisy dla tej diagnozy'}.
            Napisz to profesjonalnie po polsku."""

            payload = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "model": "openai" # Wymuszamy stabilny model na Pollinations
            }

            try:
                response = requests.post("https://text.pollinations.ai/", json=payload, timeout=45)
                
                if response.ok:
                    raw_result = response.text
                    # Uruchomienie Pancernego Parserera
                    final_doc = clean_ai_response(raw_result)
                    
                    if not final_doc or final_doc == raw_result:
                        # Ostatnia deska ratunku - proste czyszczenie jeśli parser nic nie zmienił
                        final_doc = raw_result.replace('{"role":"assistant","content":"', '').replace('"}', '')

                    st.success("✅ Dokument gotowy!")
                    
                    # Wyświetlanie w edytowalnym polu
                    edited_text = st.text_area("Treść dokumentu (możesz tu edytować):", value=final_doc, height=500)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "📥 Pobierz plik .TXT",
                            data=edited_text,
                            file_name=f"dokument_{student_name}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    with col_dl2:
                        st.info("💡 Skopiuj tekst i wklej do MS Word, aby nadać mu ostateczny wygląd.")
                else:
                    st.error("Błąd połączenia z serwerem AI. Spróbuj ponownie za chwilę.")
            
            except Exception as e:
                st.error(f"Wystąpił nieoczekiwany błąd: {str(e)}")

st.markdown("---")
st.caption("EduBox AI © 2026 | Wspieramy nauczycieli w codziennej pracy.")mport streamlit as st
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
