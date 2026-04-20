import streamlit as st
from narzedzia import call_openai_text, call_openai_image, create_word_document, extract_text_from_file
import markdown

def render_download_button(title, text, image_bytes=None):
    """Pomocniczy komponent do wyświetlania przycisku pobierania Worda"""
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
        st.info("💡 Kliknij przycisk, aby zapisać wygenerowany tekst i grafikę w pliku gotowym do druku i edycji!")

# ==========================================
# MODUŁ 1: HISTORYJKI SPOŁECZNE (+ OBRAZKI)
# ==========================================
def modul_historyjki_spoleczne(api_key, is_pro):
    st.header("🧩 Generator Historyjek Społecznych")
    st.markdown("Tworzy terapeutyczne opowiadania (Social Stories) dla dzieci w spektrum autyzmu oraz **generuje ilustrację**!")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        imie = st.text_input("Imię dziecka:")
        wiek = st.number_input("Wiek dziecka:", min_value=2, max_value=15, value=5)
        problem = st.text_area("Sytuacja problemowa (Trigger):", placeholder="Np. Zosia bardzo boi się dźwięku szkolnego dzwonka lub odkurzacza.")
        rozwiazanie = st.text_area("Oczekiwana reakcja / Strategia:", placeholder="Np. Zakładamy słuchawki wyciszające, robimy głęboki wdech.")
        
        if st.button("📖 Wygeneruj Historyjkę i Rysunek"):
            if not api_key:
                st.error("Brak klucza API OpenAI.")
            elif not is_pro:
                st.error("Funkcja generowania grafiki wymaga kodu Premium (KAWA2024).")
            elif imie and problem:
                with st.spinner("1/2 Pisanie specjalistycznej historyjki..."):
                    sys_prompt = f"""Jesteś certyfikowanym terapeutą behawioralnym. Napisz Historyjkę Społeczną dla {wiek}-letniego dziecka z autyzmem.
                    ZASADY: Krótkie akapity, język dosłowny (zero metafor).
                    STRUKTURA: 1. Fakty (gdzie, kto), 2. Perspektywa (co czują inni), 3. Dyrektywy (co zrobić krok po kroku), 4. Afirmacja."""
                    user_prompt = f"Imię: {imie}\nProblem: {problem}\nRozwiązanie: {rozwiazanie}"
                    
                    st.session_state['hist_tekst'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.5)
                
                with st.spinner("2/2 DALL-E rysuje ilustrację terapeutyczną..."):
                    img_prompt = f"Prosta, bardzo przyjazna i kolorowa ilustracja wektorowa do bajki dla dzieci. Główny motyw: dziecko, które uczy się radzić sobie z sytuacją: {problem}. Styl: bezpieczny, ciepły, uroczy, idealny dla dziecka w wieku {wiek} lat z autyzmem. ŻADNYCH NAPISÓW LUB LITER na obrazku."
                    img_bytes, err = call_openai_image(api_key, img_prompt)
                    
                    if img_bytes:
                        st.session_state['hist_obraz'] = img_bytes
                    else:
                        st.error(err)
            else: 
                st.warning("Wpisz imię i opisz problem.")

    with c2:
        if 'hist_tekst' in st.session_state:
            st.markdown("### 📚 Twoja Historyjka:")
            
            if 'hist_obraz' in st.session_state and st.session_state['hist_obraz']:
                st.image(st.session_state['hist_obraz'], caption="Ilustracja do historyjki", use_column_width=True)
            
            st.markdown(f"<div class='story-box'>{st.session_state['hist_tekst']}</div>", unsafe_allow_html=True)
            
            # Przycisk pobierania z obrazkiem!
            render_download_button("Historyjka Spoleczna", st.session_state['hist_tekst'], st.session_state.get('hist_obraz'))

# ==========================================
# MODUŁ 2: PRZEDSZKOLE (RYMOWANKI NAPRAWIONE)
# ==========================================
def modul_przedszkole(api_key):
    st.header("🎈 Asystent Przedszkolny (Rymowanki i Dyplomy)")
    st.markdown("Generuje perfekcyjne, rymowane wierszyki i dedykacje dla maluchów.")
    
    typ = st.radio("Czego potrzebujesz?", ["Wierszyk na Dyplom", "Rymowanka grupowa"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if "Dyplom" in typ:
            imie = st.text_input("Imię dziecka:")
            cechy = st.text_area("Za co nagroda / Cechy dziecka:", placeholder="Np. Jasio uwielbia dinozaury, zawsze ma uśmiech na twarzy.")
        else:
            temat = st.text_area("Jaki jest cel rymowanki?", placeholder="Np. Rymowanka o sprzątaniu zabawek z pokazywaniem gestów.")
            
        if st.button("✍️ Wymyśl Wierszyk"):
            with st.spinner("Układanie rymów dokładnych..."):
                # NAPRAWIONY, SUPER-RYGORYSTYCZNY PROMPT DO RYMÓW
                sys_prompt = """Jesteś wybitnym polskim poetą dziecięcym (poziom Juliana Tuwima). Piszesz wierszyki.
                ZASADY KRYTYCZNE, KTÓRYCH ZŁAMANIE JEST BŁĘDEM:
                1. Rymy w układzie AABB (wers 1 z 2, wers 3 z 4).
                2. Rymy muszą być DOKŁADNE i czysto polskie (np. rączki/pączki, misie/ptysie, lala/krasnala). Żadnych wymuszonych, białych rymów!
                3. Każdy wers w strofie MUST mieć bardzo zbliżoną liczbę sylab, aby zachować rytm skandowania (jak piosenka).
                Zwróć sam tekst rymowanki."""
                
                if "Dyplom" in typ:
                    user_prompt = f"Napisz wesoły 2-zwrotkowy wierszyk na dyplom. Imię: {imie}. Kontekst: {cechy}."
                else:
                    user_prompt = f"Napisz rymowankę użytkową dla grupy. Cel: {temat}. Dodaj w nawiasach instrukcje gestów."
                
                st.session_state['przedszkole_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.7)

    with c2:
        if 'przedszkole_wynik' in st.session_state:
            st.markdown("### 🎵 Twój Wierszyk:")
            st.markdown(f"<div class='story-box'>{st.session_state['przedszkole_wynik'].replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
            render_download_button("Rymowanka Przedszkolna", st.session_state['przedszkole_wynik'])

# ==========================================
# MODUŁ 3: KREATOR TUS
# ==========================================
def modul_kreator_tus(api_key):
    st.header("🎭 Kreator Zajęć TUS (Trening Umiejętności Społecznych)")
    
    col1, col2 = st.columns(2)
    with col1:
        wiek = st.text_input("Wiek grupy (np. 6-7 lat):")
        czas = st.selectbox("Czas trwania zajęć:", ["30 minut", "45 minut", "60 minut"])
        cel = st.text_area("Główny problem do przepracowania:", placeholder="Np. Agresywne zachowania po przegranej w grze.")
        
        if st.button("🧩 Generuj Scenariusz TUS"):
            if cel and wiek:
                with st.spinner("Tworzenie konspektu TUS..."):
                    sys_prompt = "Jesteś trenerem TUS. Skonstruuj scenariusz. 1. Powitanie, 2. Psychoedukacja, 3. Scenki / Ról, 4. Relaksacja, 5. Pożegnanie."
                    user_prompt = f"Wiek: {wiek}\nCzas: {czas}\nProblem: {cel}"
                    st.session_state['tus_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.6)
            else: 
                st.warning("Wypełnij wiek i cel zajęć.")
            
    with col2:
        if 'tus_wynik' in st.session_state:
            st.markdown("### 📋 Twój Scenariusz TUS:")
            st.markdown(f"<div class='a4-paper' style='min-height:auto; padding:20px;'>{markdown.markdown(st.session_state['tus_wynik'])}</div>", unsafe_allow_html=True)
            render_download_button("Scenariusz TUS", st.session_state['tus_wynik'])

# ==========================================
# MODUŁ 4: PROJEKTY BADAWCZE
# ==========================================
def modul_projekty_badawcze(api_key):
    st.header("🧪 Metoda Projektów Badawczych")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        temat = st.text_input("Temat projektu (np. Kosmos, Krowa):")
        wiek = st.text_input("Wiek dzieci:")
        
        if st.button("🔍 Opracuj Projekt"):
            if temat:
                with st.spinner("Projektowanie działań badawczych..."):
                    sys_prompt = "Jesteś metodykiem edukacji. Opracuj plan projektu badawczego: 1. Prowokacja i Siatka Pytań, 2. 3 Eksperymenty, 3. Wydarzenie kulminacyjne."
                    user_prompt = f"Temat: {temat}\nWiek: {wiek}"
                    st.session_state['projekt_wynik'] = call_openai_text(api_key, sys_prompt, user_prompt, 0.7)
            else: 
                st.warning("Podaj temat projektu!")

    with col2:
        if 'projekt_wynik' in st.session_state:
            st.markdown("### 🗺️ Plan Projektu:")
            st.markdown(f"<div class='a4-paper' style='min-height:auto; padding:20px;'>{markdown.markdown(st.session_state['projekt_wynik'])}</div>", unsafe_allow_html=True)
            render_download_button("Projekt Badawczy", st.session_state['projekt_wynik'])
