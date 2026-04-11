import streamlit as st
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
        # 1. Sprawdź czy to JSON
        data = json.loads(raw_text)
        
        if isinstance(data, dict):
            # Standard OpenAI / DeepSeek API
            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                content = msg.get("content", "")
                if not content: 
                    content = data["choices"][0].get("text", "")
                return content
            elif "content" in data:
                return data["content"]
            elif "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", raw_text)
    except:
        pass

    # 2. Jeśli JSON zawiódł, użyj Regex do wyłapania treści
    content_match = re.search(r'"content":\s*"(.*?)"', raw_text, re.DOTALL)
    if content_match:
        content = content_match.group(1)
        try:
            return content.encode().decode('unicode_escape')
        except:
            return content

    # 3. Usuwanie tagów <think>
    processed = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    
    return processed.strip()

# --- GENEROWANIE ---
if st.button("✨ Generuj Dokument", type="primary"):
    if not diagnosis.strip():
        st.warning("⚠️ Wpisz diagnozę, aby AI wiedziało na czym się skupić.")
    else:
        with st.spinner("🤖 AI pracuje nad dokumentem... Proszę czekać."):
            
            system_msg = "Jesteś ekspertem pedagogiki specjalnej w Polsce. Tworzysz profesjonalną dokumentację szkolną (IPET, WOPFU) zgodnie z rozporządzeniami MEN. Używaj języka formalnego. Zwracaj WYŁĄCZNIE czysty dokument w formacie Markdown z nagłówkami. Nie dodawaj wstępów."
            
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
                "model": "openai"
            }

            try:
                response = requests.post("https://text.pollinations.ai/", json=payload, timeout=45)
                
                if response.ok:
                    raw_result = response.text
                    final_doc = clean_ai_response(raw_result)
                    
                    if not final_doc or final_doc == raw_result:
                        final_doc = raw_result.replace('{"role":"assistant","content":"', '').replace('"}', '')

                    st.success("✅ Dokument gotowy!")
                    
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
st.caption("EduBox AI © 2026 | Wspieramy nauczycieli w codziennej pracy.")
