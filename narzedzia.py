import requests
import io
try:
    import PyPDF2
except ImportError:
    pass
try:
    import docx
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    pass

# --- FUNKCJA: GENEROWANIE TEKSTU (GPT-4o-mini) ---
def call_openai_text(api_key, system_prompt, user_prompt, temperature=0.6):
    if not api_key:
        return "Błąd: Brak klucza API OpenAI."
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": temperature
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        if response.ok:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Błąd API: {response.text}"
    except Exception as e:
        return f"Błąd komunikacji: {str(e)}"

# --- FUNKCJA: GENEROWANIE OBRAZU (DALL-E 3) ---
def call_openai_image(api_key, image_prompt):
    if not api_key:
        return None, "Brak klucza API."
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "dall-e-3",
            "prompt": image_prompt,
            "n": 1,
            "size": "1024x1024"
        }
        response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload, timeout=120)
        if response.ok:
            image_url = response.json()["data"][0]["url"]
            # Pobieramy obrazek jako ciąg bajtów (żeby móc go wstawić do Worda!)
            img_response = requests.get(image_url)
            if img_response.ok:
                return io.BytesIO(img_response.content), None
        return None, f"Błąd API Obrazów: {response.text}"
    except Exception as e:
        return None, f"Błąd komunikacji: {str(e)}"

# --- FUNKCJA: EKSPORT DO WORDA (.DOCX) ---
def create_word_document(title, content_text, image_bytes=None):
    doc = docx.Document()
    
    # Marginesy
    section = doc.sections[0]
    section.left_margin = section.right_margin = Inches(1)
    
    # Styl domyślny
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # Nagłówek
    h = doc.add_heading(title.upper(), level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("-" * 80)
    
    # Jeśli mamy wygenerowany obrazek, wstawiamy go na początku Worda
    if image_bytes:
        doc.add_picture(image_bytes, width=Inches(4.5))
        last_paragraph = doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph() # Odstęp

    # Wstawianie tekstu (z obsługą pogrubień markdown)
    for line in content_text.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue
            
        if line.startswith('### '): doc.add_heading(line[4:], level=3)
        elif line.startswith('## '): doc.add_heading(line[3:], level=2)
        elif line.startswith('# '): doc.add_heading(line[2:], level=1)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_bold_parts(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_bold_parts(p, line)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _add_bold_parts(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: run.bold = True

# --- FUNKCJA: CZYTANIE PDF/DOCX ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: 
                if para.text.strip(): text += para.text + "\n"
    except Exception:
        pass
    return text
