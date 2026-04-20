import streamlit as st
from narzedzia import call_openai_text, call_openai_image, create_word_document, extract_text_from_file
import markdown

def render_download_button(title, text, image_bytes=None):
    """Pomocniczy komponent do wyświetlania przycisku pobierania Worda i informowania o kopiowaniu"""
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    with c1:
        doc_buffer = create_word_document(title, text, image_bytes)
        st.download_button(
            label="📄 POBIERZ JAKO WORD (.DOCX)",
            data=doc_buffer,
            file_name=f"{title.replace(' ', '_').lower()}.docx",
            type="primary",
            use_container_width=True
        )
    with c2:
        st.info("💡 Kliknij przycisk po lewej, aby zapisać gotowy, sformatowany plik na dysku. Możesz też po prostu zaznaczyć tekst wyżej myszką i skopiować go do schowka (Ctrl+C).")

# ==========================================
# MODUŁ 1: ASYSTENT DOKUMENTÓW (IPET, WOPFU)
# ==========================================
def modul_asystent_dokumentow(api_key, is_pro):
    st.header("📝 Asystent Dokumentów (IPET, WOPFU)")
    st.markdown('<div class="men-badge">🏆 KLASA S: Urzędowe Formatowanie i Język Ekspercki</div>', unsafe_allow_html=True)
    
    MEN_RULES = {
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura: Zakres dostosowań, zintegrowane działania specjalistów...",
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania)": "Struktura: Indywidualne potrzeby, mocne strony, bariery...",
        "Opinia o uczniu do Poradni PPP": "Struktura: Opis funkcjonowania poznawczego, społecznego, emocjonalnego. Ton obiektywny, nieoceniający, bazujący na faktach.",
    }
    
    tab1, tab2 = st.tabs(["📁 Dane do analizy", "📄 Podgląd i Wydruk"])
    with tab1:
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Imię / Inicjały ucznia:")
            diagnosis = st.text_area("Diagnoza główna / Powód opinii:", height=100)
        with c2:
            strengths = st.text_area("💪 Mocne strony:", height=100)
            weaknesses = st.text_area("🚧 Trudności / Niepokojące zachowania:", height=100)
            
        if st.button("⚙️ GENERUJ DOKUMENT URZĘDOWY"):
            if not is_pro: st.error("Wymagany Kod Premium (KAWA2024)")
            elif not s_name or not diagnosis: st.warning("Podaj imię i diagnozę.")
            else:
                with st.spinner("Przetwarzam fachowym żargonem zgodnym z MEN..."):
                    sys_prompt = f"Jesteś wybitnym diagnostą i pedagogiem. Napisz dokument: {doc_type}. Używaj wysoce specjalistycznego żargonu pedagogicznego i psychologicznego. Zadbaj o zgodność z polskim prawem oświatowym i wytycznymi MEN."
                    user_prompt = f"Imię: {s_name}\nDiagnoza: {diagnosis}\nMocne: {strengths}\nSłabe: {weaknesses}\nWymagania: {MEN_RULES[doc_type]}"
                    result = call_openai_text(api_key, sys_prompt, user_prompt, 0.5)
                    st.session_state['gen_doc'] = result
                    st.session_state['doc_title'] = doc_type
                    st.success("✅ Gotowe! Przejdź do zakładki 'Podgląd i Wydruk'.")
                    
    with tab2:
        if 'gen_doc' in st.session_state:
            html = markdown.markdown(st.session_state['gen_doc'])
            st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
            render_download_button(st.session_state['doc_title'], st.session_state['gen_doc'])
        else:
            st.info("Wygeneruj dokument w zakładce obok.")

# ==========================================
# MODUŁ 2: HISTORYJKI SPOŁECZNE (+ OBRAZKI)
# ==========================================
def modul_historyjki_spoleczne(api_key, is_pro):
    st.header("🧩 Generator Historyjek Społecznych")
    st.markdown("Tworzy terapeutyczne opowiadania (Social Stories) dla dzieci w spektrum autyzmu oraz **generuje ilustrację** za pomocą sztucznej inteligencji!")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        imie = st.text_input("Imię dziecka:")
        wiek = st.number_input("Wiek dziecka:", min_value=2, max_value=15, value=5)
        problem = st.text_area("Sytuacja problemowa (Zapalnik/Trigger):", placeholder="Np. Zosia bardzo boi się dźwięku szkolnego dzwonka lub odkurzacza.")
        rozwiazanie = st.text_area("Oczekiwana reakcja / Strategia radzenia sobie:", placeholder="Np. Zakładamy słuchawki wyciszające, robimy głęboki wdech.")
        
        if st.button("📖 Wygeneruj Historyjkę i Obrazek"):
            if not api_key:
                st.error("Brak klucza API OpenAI.")
            elif not is_pro:
                st.error("Funkcja wymaga kodu Premium (KAWA2024).")
            elif imie and problem:
                with st.spinner("1/2 Pisanie specjalistycznej historyjki..."):
                    sys_prompt = f"""Jesteś certyfikowanym terapeutą behawioralnym. Napisz Historyjkę Społeczną dla {wiek}-letniego dziecka z autyzmem.
                    ZASADY: Krótkie akapity, język dosłowny (zero metafor i przenośni). Zwróć sam czysty tekst.
                    STRUKTURA: 1. Fakty (gdzie, kto), 2. Perspektywa (co czują inni), 3. Dyrektywy (co zrobić krok po kroku), 4. Afirmacja."""
                    user_prompt = f"Imię: {imie}\nProblem: {problem}\nRozwiązanie: {rozwiazanie}"
                    
                    st.session_state['hist_tekst'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.5)
                
                with st.spinner("2/2 Sztuczna Inteligencja maluje ilustrację terapeutyczną..."):
                    img_prompt = f"Prosta, bardzo przyjazna i kolorowa ilustracja wektorowa do bajki dla dzieci. Główny motyw: dziecko, które uczy się radzić sobie z sytuacją: {problem}. Styl: bezpieczny, ciepły, uroczy, idealny dla dziecka w wieku {wiek} lat z autyzmem. ŻADNYCH NAPISÓW LUB LITER na obrazku."
                    img_bytes, err = call_openai_image(api_key, img_prompt)
                    
                    if img_bytes:
                        st.session_state['hist_obraz'] = img_bytes
                    else:
                        st.error(f"Błąd grafiki: {err}")
            else: 
                st.warning("Wpisz imię i opisz problem.")

    with c2:
        if 'hist_tekst' in st.session_state:
            st.markdown("### 📚 Twoja Historyjka:")
            
            if 'hist_obraz' in st.session_state and st.session_state['hist_obraz']:
                st.image(st.session_state['hist_obraz'], caption="Ilustracja do historyjki (Wygenerowana przez AI)", use_column_width=True)
            
            st.markdown(f"<div class='story-box'>{st.session_state['hist_tekst']}</div>", unsafe_allow_html=True)
            
            render_download_button("Historyjka Społeczna", st.session_state['hist_tekst'], st.session_state.get('hist_obraz'))

# ==========================================
# MODUŁ 3: PRZEDSZKOLE (RYMOWANKI NAPRAWIONE)
# ==========================================
def modul_przedszkole(api_key):
    st.header("🎈 Asystent Przedszkolny (Rymowanki i Dyplomy)")
    st.markdown("Generuje perfekcyjnie rymujące się wierszyki, wyliczanki wyciszające i dedykacje dla maluchów.")
    
    typ = st.radio("Czego potrzebujesz?", ["Wierszyk na Dyplom (Spersonalizowany)", "Rymowanka grupowa (np. na wyciszenie, sprzątanie)"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if "Dyplom" in typ:
            imie = st.text_input("Imię dziecka:")
            cechy = st.text_area("Za co nagroda / Cechy dziecka:", placeholder="Np. Jasio uwielbia dinozaury, zawsze ma uśmiech na twarzy i pięknie śpiewa.")
        else:
            temat = st.text_area("Jaki jest cel rymowanki?", placeholder="Np. Krótki wierszyk o sprzątaniu zabawek z pokazywaniem gestów dla 3-latków.")
            
        if st.button("✍️ Wymyśl Wierszyk"):
            if api_key:
                with st.spinner("Układanie idealnych rymów (AABB)..."):
                    sys_prompt = """Jesteś najwybitniejszym polskim poetą dziecięcym (jak Jan Brzechwa). 
                    ZASADY KRYTYCZNE, KTÓRYCH NIE MOŻESZ ZŁAMAĆ:
                    1. Rymy muszą być DOKŁADNE, np. (kotki/płotki, lala/krasnala). Żadnych wymuszonych rymów.
                    2. Układ rymów to AABB (wers pierwszy rymuje się z drugim, a trzeci z czwartym).
                    3. Każdy wers musi mieć IDENTYCZNĄ liczbę sylab (np. dokładnie 8 sylab), aby wierszyk był bardzo rytmiczny i przypominał piosenkę.
                    Zwróć sam tekst rymowanki."""
                    
                    if "Dyplom" in typ:
                        user_prompt = f"Napisz wesoły 2-zwrotkowy wierszyk na dyplom dla dziecka. Imię: {imie}. Cechy/Kontekst: {cechy}."
                    else:
                        user_prompt = f"Napisz rytmiczną rymowankę użytkową dla grupy przedszkolaków. Temat/Cel: {temat}. Dodaj w nawiasach instrukcje gestów (np. klaskanie) dla nauczyciela."
                    
                    st.session_state['przedszkole_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.7)
            else:
                st.warning("Brak klucza API.")

    with c2:
        if 'przedszkole_wynik' in st.session_state:
            st.markdown("### 🎵 Twój Wierszyk:")
            # Używamy st.code dla błyskawicznego kopiowania!
            st.code(st.session_state['przedszkole_wynik'], language="text")
            render_download_button("Rymowanka", st.session_state['przedszkole_wynik'])

# ==========================================
# MODUŁ 4: KREATOR TUS
# ==========================================
def modul_kreator_tus(api_key):
    st.header("🎭 Kreator Zajęć TUS (Trening Umiejętności Społecznych)")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        wiek = st.text_input("Wiek grupy (np. 6-7 lat):")
        czas = st.selectbox("Czas trwania zajęć:", ["30 minut", "45 minut", "60 minut"])
        cel = st.text_area("Główny problem do przepracowania:", placeholder="Np. Agresywne zachowania po przegranej w grze planszowej. Trudność z czekaniem na swoją kolej.")
        
        if st.button("🧩 Generuj Scenariusz TUS"):
            if cel and wiek:
                with st.spinner("Tworzenie konspektu TUS..."):
                    sys_prompt = "Jesteś certyfikowanym trenerem TUS. Skonstruuj praktyczny scenariusz. Struktura: 1. Powitanie i Rundka, 2. Psychoedukacja, 3. Scenki / Odgrywanie Ról (podaj 2 scenki), 4. Relaksacja, 5. Pożegnanie. Zadbaj o zgodność z metodyką nauczania."
                    user_prompt = f"Wiek: {wiek}\nCzas: {czas}\nProblem do przepracowania: {cel}"
                    st.session_state['tus_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.6)
            else: 
                st.warning("Wypełnij wiek i cel zajęć.")
            
    with col2:
        if 'tus_wynik' in st.session_state:
            st.markdown("### 📋 Twój Scenariusz TUS:")
            st.markdown(f"<div class='a4-paper' style='min-height:auto; padding:30px;'>{markdown.markdown(st.session_state['tus_wynik'])}</div>", unsafe_allow_html=True)
            render_download_button("Scenariusz TUS", st.session_state['tus_wynik'])

# ==========================================
# MODUŁ 5: KOMUNIKACJA Z RODZICEM
# ==========================================
def modul_trudny_rodzic(api_key):
    st.header("🤝 Asystent Komunikacji z Rodzicem (Tłumacz)")
    st.markdown("Zastąp swoje nerwy uprzejmą i profesjonalną dyplomacją (idealne do e-dziennika).")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        ton_wypowiedzi = st.selectbox("Wybierz cel i ton wiadomości:", [
            "Uprzejma prośba o interwencję (np. złe zachowanie)",
            "Stanowcze przypomnienie o zasadach (np. chore dzieci w placówce)",
            "Zawiadomienie o problemach w nauce",
            "Zaproszenie na trudną rozmowę"
        ])
        
        surowy_tekst = st.text_area("Co chcesz przekazać rodzicowi? (Napisz w nerwach, swoimi słowami):", height=150, 
                                    placeholder="Np. Pani syn znowu przyszedł chory. Ma gila do pasa i zarazi wszystkie inne dzieci!")
        
        if st.button("✨ Przetłumacz na język dyplomacji"):
            if surowy_tekst:
                with st.spinner("Redagowanie wiadomości..."):
                    sys_prompt = f"Jesteś empatycznym, asertywnym pedagogiem. Przetłumacz emocjonalny tekst na profesjonalną, formalną wiadomość e-dziennika. Cel: {ton_wypowiedzi}. Stosuj tzw. 'metodę kanapki' (pozytyw-problem-pozytyw). Zwróć tylko gotowy tekst bez komentarza."
                    st.session_state['tlumacz_wynik'] = call_openai_text(api_key, sys_prompt, surowy_tekst, 0.7)
            else: st.warning("Wpisz najpierw swoją myśl!")

    with c2:
        if 'tlumacz_wynik' in st.session_state:
            st.markdown("### 📩 Gotowa wiadomość (do skopiowania):")
            st.code(st.session_state['tlumacz_wynik'], language="text")
            st.info("Zarządzanie komunikacją zgodnie ze standardami pracy szkoły.")
