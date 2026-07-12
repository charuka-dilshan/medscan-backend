import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_prescription_text(raw_ocr_text: str):
    system_prompt = """
        You are a strict Sri Lankan medical AI assistant. Extract info from the provided raw OCR text.
        - Normalize drug names.
        - If unclear, return 'Not specified'.
        - Output ONLY valid JSON matching this schema:
        {
            "pill_name": "...",
            "dosage": "...",
            "frequency": "...",
            "instructions_english": "...",
            "instructions_sinhala": "...",
            "instructions_tamil": "...",
            "lifestyle_guidance": "..."
        }
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Raw Prescription Text:\n{raw_ocr_text}"}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        return {"error": "Failed to parse data"}