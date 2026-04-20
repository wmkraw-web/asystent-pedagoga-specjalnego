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
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura: Zakres dostosowań, zintegrowane działania specjalistów, ocena efektywności.",
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania)": "Struktura: Indywidualne potrzeby, mocne strony, bariery, przyczyny niepowodzeń.",
        "Opinia o uczniu do Poradni PPP": "Struktura: Opis funkcjonowania poznawczego, społecznego, emocjonalnego. Ton obiektywny, nieoceniający, bazujący na faktach.",
    }
    
    tab1, tab2 = st.tabs(["📁 Dane do analizy", "📄 Podgląd i Wydruk"])
    with tab1:
        doc_type = st.selectbox("Rodzaj dokumentu:", list(MEN_RULES.keys()))
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Imię / Inicjały ucznia:")
            diagnosis = st.text_area("Diagnoza główna / Powód opinii:", height=100)
            strengths = st.text_area("💪 Mocne strony:", height=100)
            weaknesses = st.text_area("🚧 Trudności / Niepokojące zachowania:", height=100)
        with c2:
            files = st.file_uploader("Wgraj orzeczenia z Poradni do analizy (Opcjonalnie PDF/DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
            custom_template = st.text_area("📋 Wklej wzór / strukturę wymaganą w Twojej placówce (Opcjonalnie):", placeholder="np. 1. Funkcjonowanie społeczne, 2. Motoryka, 3. Zalecenia...", height=230)
            
        if st.button("⚙️ GENERUJ DOKUMENT URZĘDOWY"):
            if not is_pro: st.error("Wymagany aktywny Kod Premium. Odblokuj pełen dostęp wspierając projekt!")
            elif not s_name or not diagnosis: st.warning("Podaj imię i diagnozę.")
            else:
                with st.spinner("Przetwarzam fachowym żargonem zgodnym z MEN i analizuję pliki..."):
                    full_text = ""
                    if files:
                        for f in files: full_text += f"\n[ANALIZA PLIKU: {f.name}]\n" + extract_text_from_file(f)
                    
                    template_instruction = f"WYMAGANA STRUKTURA DOKUMENTU: Należy BEZWZGLĘDNIE zastosować poniższy układ i szczegółowo go wypełnić:\n{custom_template}" if custom_template.strip() else f"WYMAGANIA MEN: {MEN_RULES[doc_type]}"

                    sys_prompt = f"""Jesteś wybitnym diagnostą i pedagogiem. Napisz BARDZO SZCZEGÓŁOWY i ROZBUDOWANY dokument: {doc_type}. 
                    Używaj wysoce specjalistycznego żargonu pedagogicznego i psychologicznego. Zadbaj o zgodność z polskim prawem oświatowym i wytycznymi MEN.
                    Dokument ma być wyczerpujący, analityczny i zawierać konkretne wskazówki do pracy. Unikaj powierzchownych, jednozdaniowych haseł.
                    ZASADY: 1. {template_instruction}"""
                    
                    user_prompt = f"Imię: {s_name}\nDiagnoza: {diagnosis}\nMocne: {strengths}\nSłabe: {weaknesses}\nPliki do analizy: {full_text[:15000]}"
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
    st.markdown("Tworzy szczegółowe opowiadania (Social Stories) dla dzieci oraz **generuje grafiki przyczynowo-skutkowe**!")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        imie = st.text_input("Imię dziecka:")
        wiek = st.number_input("Wiek dziecka:", min_value=2, max_value=15, value=5)
        problem = st.text_area("Sytuacja problemowa (Zapalnik/Trigger):", placeholder="Np. Zosia bardzo boi się dźwięku odkurzacza.")
        rozwiazanie = st.text_area("Oczekiwana reakcja / Strategia radzenia sobie:", placeholder="Np. Zakładamy słuchawki wyciszające, idziemy do drugiego pokoju.")
        
        if st.button("📖 Wygeneruj Historyjkę i Obrazek"):
            if not api_key:
                st.error("Brak klucza API OpenAI.")
            elif not is_pro:
                st.error("Funkcja wymaga aktywnego Kodu Premium. Odblokuj pełen dostęp wspierając projekt!")
            elif imie and problem:
                with st.spinner("1/2 Pisanie rozbudowanej historyjki..."):
                    sys_prompt = f"""Jesteś certyfikowanym terapeutą behawioralnym. Napisz SZCZEGÓŁOWĄ i ROZBUDOWANĄ Historyjkę Społeczną dla {wiek}-letniego dziecka z autyzmem.
                    ZASADY: Język dosłowny (zero metafor). Zwróć sam czysty tekst, używaj wyraźnych akapitów.
                    WYMAGANA STRUKTURA: 
                    1. Wstęp (kim jest bohater, co lubi).
                    2. Sytuacja (gdzie jest i co dokładnie się dzieje).
                    3. Uczucie (nazwanie emocji - np. strach, złość).
                    4. Rozwiązanie / Strategia (co zrobić krok po kroku).
                    5. Afirmacja (sukces, poczucie bezpieczeństwa)."""
                    user_prompt = f"Imię: {imie}\nProblem: {problem}\nRozwiązanie: {rozwiazanie}"
                    
                    st.session_state['hist_tekst'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.6)
                
                with st.spinner("2/2 Nowy model AI maluje ilustrację..."):
                    # CAŁKOWICIE NOWY PROMPT: Blokada słów takich jak "sytuacja", "strategia", czy "panel", które AI próbowało napisać jako tytuły.
                    img_prompt = f"A completely wordless picture book illustration divided visually in half. First half: A {wiek}-year-old child reacting to {problem}. Any scary object must look completely normal and inanimate (no faces, no eyes). Second half: The same child doing {rozwiazanie}. Style: flat vector, minimalist pastel colors, cute aesthetic. ABSOLUTELY NO BANNERS, NO TITLES, NO LABELS, NO SPEECH BUBBLES, NO TEXT."
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
                st.image(st.session_state['hist_obraz'], caption="Ilustracja wizualna (Problem ➡️ Rozwiązanie)", use_column_width=True)
            
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
                with st.spinner("Układanie logicznych rymów (AABB)..."):
                    sys_prompt = """Jesteś autorem bardzo prostych rymowanek dla dzieci w wieku przedszkolnym.
                    ZASADY KRYTYCZNE:
                    1. Pisz tylko i wyłącznie w układzie AABB (wers 1 musi rymować się z 2, a wers 3 z 4).
                    2. Używaj najprostszych, bardzo dokładnych rymów (np. krok/smok, woda/zgoda, dzieci/śmieci). 
                    3. Zdania muszą być krótkie, łatwe do wypowiedzenia i rytmiczne.
                    4. Odrzuć trudne słowa, dziwne metafory i tzw. rymy niedokładne. Skup się w 100% na tym, aby na końcu wersów były czyste rymy.
                    Zwróć sam tekst rymowanki, bez komentarzy."""
                    
                    if "Dyplom" in typ:
                        user_prompt = f"Napisz prosty 2-zwrotkowy wierszyk na dyplom dla dziecka. Imię: {imie}. Cechy/Kontekst: {cechy}."
                    else:
                        user_prompt = f"Napisz rytmiczną rymowankę użytkową dla grupy przedszkolaków. Temat/Cel: {temat}. Dodaj w nawiasach instrukcje gestów (np. klaskanie) dla nauczyciela."
                    
                    st.session_state['przedszkole_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.2)
            else:
                st.warning("Brak klucza API.")

    with c2:
        if 'przedszkole_wynik' in st.session_state:
            st.markdown("### 🎵 Twój Wierszyk:")
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
        stan_dziecka = st.text_area("Profil grupy / Stan dzieci (Opcjonalnie):", placeholder="Np. norma intelektualna, dzieci w spektrum autyzmu, dzieci z ADHD, mutyzm...")
        
        if st.button("🧩 Generuj Rozbudowany Scenariusz TUS"):
            if cel and wiek:
                with st.spinner("Tworzenie bardzo szczegółowego konspektu TUS..."):
                    sys_prompt = """Jesteś certyfikowanym trenerem TUS. Skonstruuj BARDZO SZCZEGÓŁOWY i praktyczny scenariusz. 
                    Struktura: 
                    1. Powitanie i Rundka (opis ćwiczenia).
                    2. Psychoedukacja (jak wytłumaczyć temat dzieciom).
                    3. Scenki / Odgrywanie Ról (podaj 2 KONKRETNE scenki z propozycjami dialogów dla prowadzącego i dzieci).
                    4. Relaksacja (dokładny przebieg).
                    5. Pożegnanie. 
                    Zadbaj o pełne dostosowanie proponowanych metod i słownictwa do profilu grupy (stanu dzieci)."""
                    
                    user_prompt = f"Wiek: {wiek}\nCzas: {czas}\nProblem do przepracowania: {cel}\nProfil grupy / Stan dzieci: {stan_dziecka if stan_dziecka else 'Norma intelektualna'}"
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
