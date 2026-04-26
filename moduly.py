import streamlit as st
from narzedzia import call_openai_text, call_openai_image, create_word_document, extract_text_from_file
import markdown

def render_download_button(title, text, image_bytes=None, image_bytes2=None):
    """Pomocniczy komponent do wyświetlania przycisku pobierania Worda i informowania o kopiowaniu"""
    st.markdown("---")
    c1, c2 = st.columns([1, 2])
    with c1:
        doc_buffer = create_word_document(title, text, image_bytes, image_bytes2)
        st.download_button(
            label="📄 POBIERZ JAKO WORD (.DOCX)",
            data=doc_buffer,
            file_name=f"{title.replace(' ', '_').lower()}.docx",
            type="primary",
            use_container_width=True
        )
    with c2:
        st.info("💡 Kliknij przycisk po lewej, aby zapisać sformatowany plik gotowy do edycji w Wordzie.")

# ==========================================
# MODUŁ 1: ASYSTENT DOKUMENTÓW (IPET, WOPFU)
# ==========================================
def modul_asystent_dokumentow(api_key, is_pro):
    st.header("📝 Asystent Pedagoga PRO (Dokumenty SPE)")
    st.markdown('<div class="men-badge">🏆 KLASA S: Urzędowe Formatowanie, Ochrona RODO i Język Ekspercki</div>', unsafe_allow_html=True)
    
    MEN_RULES = {
        "IPET (Indywidualny Program Edukacyjno-Terapeutyczny)": "Struktura musi BEZWZGLĘDNIE obejmować: 1. Rozpoznanie i diagnozę. 2. Cele edukacyjno-terapeutyczne (ogólne i szczegółowe). 3. Metody i formy pracy. 4. Zakres dostosowań wymagań edukacyjnych. 5. Zintegrowane działania nauczycieli i specjalistów. 6. Formy i okres udzielania pomocy psychologiczno-pedagogicznej. 7. Współpracę z rodzicami.",
        "WOPFU (Wielospecjalistyczna Ocena Poziomu Funkcjonowania Ucznia)": "Struktura musi BEZWZGLĘDNIE obejmować: 1. Indywidualne potrzeby rozwojowe i edukacyjne. 2. Mocne strony, predyspozycje i uzdolnienia. 3. Przyczyny niepowodzeń edukacyjnych lub trudności. 4. Bariery i ograniczenia w środowisku ucznia. 5. Wnioski i zalecenia do dalszej pracy.",
        "Opinia o uczniu do Poradni (PPP)": "Struktura opinii: 1. Opis funkcjonowania poznawczego. 2. Funkcjonowanie społeczno-emocjonalne. 3. Motoryka i samodzielność. 4. Podsumowanie i wnioski nauczyciela.",
        "Arkusz Obserwacji / Notatka służbowa": "Opis faktograficzny sytuacji, obserwacja zachowań, zastosowane środki zaradcze, wnioski.",
        "Indywidualny Plan Wsparcia (Inny)": "Dopasuj elastycznie do potrzeb opartych na podanej diagnozie i mocnych/słabych stronach ucznia."
    }

    st.warning("🛡️ **Ochrona Danych (RODO):** Nigdy nie wpisuj pełnego imienia i nazwiska ucznia. Używaj wyłącznie inicjałów (np. 'Kasia N.').")

    tab1, tab2 = st.tabs(["📁 Krok 1: Wypełnij dane", "📄 Krok 2: Podgląd i Wydruk"])
    with tab1:
        doc_type = st.selectbox("Rodzaj dokumentu (Wymogi MEN wbudowane):", list(MEN_RULES.keys()))
        
        c1, c2 = st.columns(2)
        with c1:
            s_name = st.text_input("Inicjały Ucznia:", placeholder="np. Jan K.")
            s_age = st.text_input("Wiek / Klasa:", placeholder="np. 9 lat, Klasa 3b")
            diagnosis = st.text_area("Diagnoza główna / Powód opinii:", placeholder="Np. Spektrum autyzmu, ADHD, trudności z koncentracją...", height=80)
            strengths = st.text_area("💪 Mocne strony / Zasoby (Potencjał):", placeholder="Zainteresowania, dobre cechy, to co wychodzi mu najlepiej...", height=100)
            weaknesses = st.text_area("🚧 Trudności / Bariery (Dysfunkcje):", placeholder="Co sprawia największy problem na lekcjach lub przerwach...", height=100)
        
        with c2:
            st.markdown("### Ustawienia Zaawansowane")
            format_length = st.radio("Długość dokumentu:", ["Epicko rozbudowany (Lany tekst z żargonem)", "Zwięzły (Krótkie punkty)"])
            custom_template = st.text_area("📋 Szablon Twojej placówki (Opcjonalnie):", placeholder="Wklej tu nazwy nagłówków wymaganych w Twojej szkole (np. 1. Cele, 2. Metody, 3. Tabela z oceną)... AI się do tego dostosuje!", height=135)
            files = st.file_uploader("Wgraj orzeczenia z Poradni (Opcjonalnie PDF/DOCX):", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
            
        if st.button("✨ GENERUJ DOKUMENT URZĘDOWY"):
            if not is_pro: 
                st.error("Wymagany aktywny Kod Premium! Odblokuj pełen dostęp wspierając projekt.")
            elif not s_name or not diagnosis: 
                st.warning("Podaj inicjały ucznia i główną diagnozę.")
            else:
                with st.spinner("Analizuję wymogi MEN, dobieram żargon pedagogiczny i układam dokument... To zajmie ok. 15 sekund."):
                    full_text = ""
                    if files:
                        for f in files: full_text += f"\n[ANALIZA PLIKU: {f.name}]\n" + extract_text_from_file(f)
                    
                    length_instruction = "Wymagam BARDZO ROZBUDOWANEGO, wyczerpującego i profesjonalnego dokumentu. Każdy punkt musi być opisany w formie pełnych, bogatych w żargon pedagogiczny akapitów. Dokument ma wyglądać na stworzony przez eksperta z wieloletnim stażem." if "Epicko" in format_length else "Wymagam ZWIĘZŁEGO dokumentu (skrócona forma). Używaj punktatorów i krótkich, konkretnych zdań. Sama esencja."

                    template_instruction = f"ZIGNORUJ STANDARDOWE WYTYCZNE. Musisz BEZWZGLĘDNIE dostosować wygenerowany dokument do tego SZABLONU PLACÓWKI wymaganego przez użytkownika:\n{custom_template}" if custom_template.strip() else f"WYTYCZNE MEN DLA TEGO DOKUMENTU: {MEN_RULES[doc_type]}"

                    sys_prompt = f"""Jesteś najwyższej klasy polskim pedagogiem specjalnym, diagnostą i ekspertem ds. edukacji włączającej. Twoim zadaniem jest napisanie oficjalnego dokumentu: {doc_type}.
                    ZASADY KRYTYCZNE:
                    1. Używaj wyłącznie wysoce profesjonalnego żargonu psychologiczno-pedagogicznego. Zamiast "bywa niegrzeczny", pisz "wykazuje trudności w samoregulacji emocjonalnej".
                    2. {length_instruction}
                    3. {template_instruction}
                    4. Zwróć tylko czysty tekst dokumentu sformatowany w języku Markdown (używaj # i ## do nagłówków, ** do pogrubień). Nie dodawaj żadnych powitań typu 'Oto twój dokument'."""
                    
                    user_prompt = f"DANE UCZNIA:\nInicjały: {s_name}\nWiek/Klasa: {s_age}\n\nDIAGNOZA GŁÓWNA:\n{diagnosis}\n\nMOCNE STRONY:\n{strengths}\n\nTRUDNOŚCI:\n{weaknesses}\n\nPLIKI DO ANALIZY:\n{full_text[:15000]}"
                    
                    result = call_openai_text(api_key, sys_prompt, user_prompt, 0.4) # Niższa temperatura = bardziej formalny tekst
                    st.session_state['gen_doc'] = result
                    st.session_state['doc_title'] = f"{doc_type.split(' ')[0]} - {s_name}"
                    st.success("✅ Gotowe! Dokument sformatowany i napisany eksperckim żargonem. Przejdź do zakładki 'Podgląd i Wydruk'.")
                    
    with tab2:
        if 'gen_doc' in st.session_state:
            html = markdown.markdown(st.session_state['gen_doc'], extensions=['tables'])
            st.markdown(f'<div class="a4-paper">{html}</div>', unsafe_allow_html=True)
            render_download_button(st.session_state['doc_title'], st.session_state['gen_doc'])
        else:
            st.info("Wypełnij formularz w zakładce 'Krok 1' i kliknij przycisk generowania.")

# ==========================================
# MODUŁ 2: HISTORYJKI SPOŁECZNE (+ OBRAZKI)
# ==========================================
def modul_historyjki_spoleczne(api_key, is_pro):
    st.header("🧩 Generator Historyjek Społecznych")
    st.markdown("Tworzy szczegółowe opowiadania (Social Stories) dla dzieci oraz **generuje dwie osobne ilustracje** (Problem i Rozwiązanie)!")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        imie = st.text_input("Imię dziecka:")
        wiek = st.number_input("Wiek dziecka:", min_value=2, max_value=15, value=5)
        plec = st.radio("Płeć bohatera na ilustracji:", ["Chłopiec", "Dziewczynka"], horizontal=True)
        problem = st.text_area("Sytuacja problemowa (Zapalnik/Trigger):", placeholder="Np. Zosia bardzo boi się dźwięku odkurzacza.")
        rozwiazanie = st.text_area("Oczekiwana reakcja / Strategia radzenia sobie:", placeholder="Np. Zakładamy słuchawki wyciszające, idziemy do drugiego pokoju.")
        
        if st.button("📖 Wygeneruj Historyjkę i 2 Obrazki"):
            if not api_key:
                st.error("Brak klucza API OpenAI.")
            elif not is_pro:
                st.error("Funkcja wymaga aktywnego Kodu Premium. Odblokuj pełen dostęp wspierając projekt!")
            elif imie and problem:
                plec_en = "boy" if plec == "Chłopiec" else "girl"
                
                with st.spinner("1/3 Pisanie rozbudowanej historyjki..."):
                    sys_prompt = f"""Jesteś certyfikowanym terapeutą behawioralnym. Napisz SZCZEGÓŁOWĄ i ROZBUDOWANĄ Historyjkę Społeczną dla {wiek}-letniego dziecka ({plec}) z autyzmem.
                    ZASADY: Język dosłowny (zero metafor). Zwróć sam czysty tekst, używaj wyraźnych akapitów.
                    WYMAGANA STRUKTURA: 
                    1. Wstęp (kim jest bohater, co lubi).
                    2. Sytuacja (gdzie jest i co dokładnie się dzieje).
                    3. Uczucie (nazwanie emocji - np. strach, złość).
                    4. Rozwiązanie / Strategia (co zrobić krok po kroku).
                    5. Afirmacja (sukces, poczucie bezpieczeństwa)."""
                    user_prompt = f"Imię: {imie}\nProblem: {problem}\nRozwiązanie: {rozwiazanie}"
                    
                    st.session_state['hist_tekst'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.6)
                
                with st.spinner("2/3 AI maluje obrazek nr 1 (Problem)..."):
                    img_prompt_prob = f"A single, beautiful, wordless children's book illustration. A {wiek}-year-old {plec_en} is looking anxious because of: {problem}. The object MUST look completely normal, harmless, and inanimate (no faces, no monsters). Style: cozy, flat vector, bright pastel colors, cute aesthetic. CRITICAL RULES: 100% SINGLE SCENE. NO split screens. ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS."
                    img_prob_bytes, err1 = call_openai_image(api_key, img_prompt_prob)
                    if img_prob_bytes:
                        st.session_state['hist_obraz_prob'] = img_prob_bytes
                    else:
                        st.error(f"Błąd grafiki (Problem): {err1}")

                with st.spinner("3/3 AI maluje obrazek nr 2 (Rozwiązanie)..."):
                    img_prompt_sol = f"A single, beautiful, wordless children's book illustration. The same {wiek}-year-old {plec_en} is feeling safe, calm, and happy because they are using their coping strategy: {rozwiazanie}. In the background, the object they were afraid of ({problem}) is visible but looks completely normal and inanimate. Style: cozy, flat vector, bright pastel colors, cute aesthetic. CRITICAL RULES: 100% SINGLE SCENE. NO split screens. ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS."
                    img_sol_bytes, err2 = call_openai_image(api_key, img_prompt_sol)
                    if img_sol_bytes:
                        st.session_state['hist_obraz_sol'] = img_sol_bytes
                    else:
                        st.error(f"Błąd grafiki (Rozwiązanie): {err2}")
            else: 
                st.warning("Wpisz imię i opisz problem.")

    with c2:
        if 'hist_tekst' in st.session_state:
            st.markdown("### 📚 Twoja Historyjka:")
            
            if 'hist_obraz_prob' in st.session_state and 'hist_obraz_sol' in st.session_state:
                col_img1, col_img2 = st.columns(2)
                with col_img1:
                    st.image(st.session_state['hist_obraz_prob'], caption="Sytuacja trudna (Problem)", use_column_width=True)
                with col_img2:
                    st.image(st.session_state['hist_obraz_sol'], caption="Pożądana reakcja (Rozwiązanie)", use_column_width=True)
            
            st.markdown(f"<div class='story-box'>{st.session_state['hist_tekst']}</div>", unsafe_allow_html=True)
            
            render_download_button("Historyjka Społeczna", st.session_state['hist_tekst'], st.session_state.get('hist_obraz_prob'), st.session_state.get('hist_obraz_sol'))

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
