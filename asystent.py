import streamlit as st
import urllib.parse
import requests
import io

# --- BEZPIECZNE IMPORTY DO OBSŁUGI PLIKÓW ---
try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Asystent Pedagoga", page_icon="👩‍🏫", layout="wide")

# --- NAGŁÓWEK ---
st.title("Asystent Pedagoga 👩‍🏫")

# ROZWINIĘCIE ROZPORZĄDZENIA ZGODNIE Z PROŚBĄ
st.markdown("#### Inteligentne wsparcie pedagoga")
st.markdown("*(Zgodny z Rozporządzeniem Ministra Edukacji Narodowej z dnia 9 sierpnia 2017 r. w sprawie warunków organizowania kształcenia, wychowania i opieki dla dzieci i młodzieży niepełnosprawnych, niedostosowanych społecznie i zagrożonych niedostosowaniem społecznym)*")
st.write("---")
st.write("Wypełnij poniższe dane w punktach lub hasłowo. Sztuczna Inteligencja wygeneruje dla Ciebie profesjonalny, ciągły szkic dokumentu, który łatwo skopiujesz do Worda.")

# --- WYBÓR DOKUMENTU ---
doc_type = st.selectbox(
    "Wybierz rodzaj dokumentu do wygenerowania:",
    [
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)",
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)",
        "Ocena efektywności IPET / Realizacja",
        "Informacja o gotowości dziecka do podjęcia nauki w szkole",
        "Opinia ogólna o uczniu/wychowanku"
    ]
)

st.write("---")

# --- FORMULARZ DANYCH PODSTAWOWYCH ---
col1, col2 = st.columns(2)

with col1:
    student_name = st.text_input("Imię ucznia (lub inicjały):", placeholder="np. Jan Kowalski")
    student_age = st.text_input("Wiek i klasa/grupa:", placeholder="np. 6 lat, grupa przedszkolna 'Żabki'")
    diagnosis = st.text_area("Podstawa objęcia wsparciem (Diagnoza / Orzeczenie):", placeholder="np. Orzeczenie o potrzebie kształcenia specjalnego ze względu na autyzm (w tym zespół Aspergera)...", height=150)

with col2:
    strengths = st.text_area("Mocne strony, uzdolnienia i potencjał ucznia:", placeholder="np. Bardzo dobra pamięć wzrokowa, bogate słownictwo, chęć do budowania z klocków...", height=110)
    weaknesses = st.text_area("Trudności, bariery i wyzwania:", placeholder="np. Trudności ze skupieniem uwagi na zadaniu, impulsywność, problemy w relacjach z rówieśnikami...", height=110)

st.write("---")

# --- DODATKOWE DOKUMENTY DO ANALIZY ---
st.markdown("#### 📎 Dodatkowe dokumenty do analizy (Opcjonalne)")
st.write("Wgraj pliki z opinią z Poradni Psychologiczno-Pedagogicznej (PPP) lub wklej notatki. AI przeanalizuje te informacje i uwzględni je w tworzonym dokumencie.")

col3, col4 = st.columns(2)
with col3:
    uploaded_files = st.file_uploader("Wgraj dokumenty (PDF, DOCX, TXT):", type=["pdf", "docx", "txt"], accept_multiple_files=True)
with col4:
    additional_context = st.text_area("Lub wklej fragmenty tekstu ręcznie tutaj:", placeholder="Skopiuj i wklej fragmenty orzeczenia, starych ocen opisowych itp...", height=100)

# --- PRZYCISK GENEROWANIA ---
if st.button("Generuj dokument (AI)", type="primary", use_container_width=True):
    if not student_name or not diagnosis:
        st.warning("Uzupełnij przynajmniej Imię ucznia oraz Diagnozę, aby AI miało podstawy do napisania dokumentu!")
    else:
        with st.spinner("Sztuczna Inteligencja redaguje profesjonalny dokument... To zajmie od 10 do 30 sekund ⏳"):
            
            # --- EKSTRAKCJA TEKSTU Z PLIKÓW ---
            extracted_text = ""
            if uploaded_files:
                for file in uploaded_files:
                    if file.name.endswith('.txt'):
                        extracted_text += f"\n--- Dokument: {file.name} ---\n"
                        extracted_text += file.getvalue().decode("utf-8", errors="ignore")
                    elif file.name.endswith('.pdf') and HAS_PYPDF:
                        try:
                            pdf_reader = PyPDF2.PdfReader(file)
                            extracted_text += f"\n--- Dokument: {file.name} ---\n"
                            for page in pdf_reader.pages:
                                extracted_text += page.extract_text() + "\n"
                        except Exception as e:
                            extracted_text += f"\n[Błąd odczytu PDF: {file.name}]\n"
                    elif file.name.endswith('.docx') and HAS_DOCX:
                        try:
                            doc = docx.Document(file)
                            extracted_text += f"\n--- Dokument: {file.name} ---\n"
                            for para in doc.paragraphs:
                                extracted_text += para.text + "\n"
                        except Exception as e:
                            extracted_text += f"\n[Błąd odczytu DOCX: {file.name}]\n"
                    else:
                        extracted_text += f"\n[Załączono plik {file.name}, ale serwer nie posiada odpowiednich bibliotek do jego analizy. Użyj formatu TXT lub pola tekstowego obok.]\n"

            # --- BUDOWANIE INSTRUKCJI DLA AI (PROMPT) ---
            prompt = f"""
            Jesteś profesjonalnym polskim pedagogiem specjalnym. Twoim zadaniem jest napisanie dokumentu: "{doc_type}".
            Dane dziecka/ucznia: {student_name}, Wiek/Grupa: {student_age}.
            Podstawa objęcia wsparciem / Diagnoza: {diagnosis}.
            Mocne strony i zasoby: {strengths}.
            Trudności i bariery: {weaknesses}.
            
            Wymogi:
            1. Używaj wysoce profesjonalnego, formalnego i obiektywnego języka pedagogicznego (specyficznego dla polskich szkół i rozporządzeń MEN).
            2. Dokument musi być sformatowany logicznie (wstęp, rozwinięcie, wnioski/zalecenia).
            3. Jeśli to IPET, skup się na dostosowaniach i celach terapeutycznych. Jeśli to WOPFU, skup się na ocenie poziomu funkcjonowania. Jeśli to gotowość szkolna, opisz dojrzałość emocjonalną, poznawczą i motoryczną.
            4. Zwróć tylko sam gotowy tekst dokumentu. Bez powitań.
            """

            # Jeśli są dodatkowe załączniki, dopisz je do polecenia
            if extracted_text or additional_context:
                prompt += f"\n\n--- WAŻNE: PONIŻEJ ZNAJDUJĄ SIĘ DODATKOWE INFORMACJE O DZIECKU Z ZAŁĄCZONYCH DOKUMENTÓW (np. opinii z PPP). BAZUJ NA NICH PODCZAS PISANIA NOWEGO DOKUMENTU: ---\n"
                if additional_context:
                    prompt += additional_context + "\n"
                if extracted_text:
                    prompt += extracted_text + "\n"

            try:
                # Korzystamy z darmowego generatora tekstu
                encoded_prompt = urllib.parse.quote(prompt)
                url = f"https://text.pollinations.ai/prompt/{encoded_prompt}"
                
                # Ustawiamy timeout na 60 sekund w razie obciążenia
                response = requests.get(url, timeout=60)

                if response.status_code == 200:
                    generated_text = response.text
                    
                    st.success(f"Sukces! Twój dokument ({doc_type}) został wygenerowany.")
                    
                    # Pole tekstowe z wynikiem
                    st.text_area("Gotowy tekst (Kliknij w środek, wciśnij Ctrl+A, a potem Ctrl+C, żeby skopiować):", value=generated_text, height=500)
                    
                    # Opcja pobrania jako plik
                    st.download_button(
                        label="💾 Pobierz dokument jako plik tekstowy (.txt)",
                        data=generated_text,
                        file_name=f"{doc_type.split()[0]}_{student_name.replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.error("Serwer AI jest w tej chwili obciążony. Proszę, kliknij generuj ponownie za kilkanaście sekund.")
            except Exception as e:
                st.error("Przekroczono czas oczekiwania na serwer lub wystąpił błąd połączenia. Spróbuj ponownie!")

st.write("---")
st.caption("Pamiętaj: Wygenerowany dokument ma charakter poglądowy i szkicowy. Zawsze przeczytaj go uważnie i dostosuj ostateczną treść do indywidualnych, rzeczywistych potrzeb i sytuacji dziecka przed włączeniem do oficjalnej dokumentacji szkolnej.")
