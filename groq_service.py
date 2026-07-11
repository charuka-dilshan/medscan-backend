import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_prescription_text(raw_ocr_text: str):
    """
    Uses Groq (Llama 3) to convert messy OCR text into structured JSON 
    with Sinhala, Tamil, and Sri Lankan dietary context.
    """
    system_prompt = """
    You are an expert Sri Lankan medical AI assistant.
    Analyze the raw prescription text provided and return ONLY a valid JSON object matching this structure:
    {
      "pill_name": "Name of medication",
      "dosage": "e.g., 500mg",
      "frequency": "e.g., Twice daily after meals",
      "instructions_english": "Detailed English instructions",
      "instructions_sinhala": "Sinhala translation of instructions",
      "instructions_tamil": "Tamil translation of instructions",
      "lifestyle_guidance": "Sri Lankan dietary warnings (e.g., Avoid with curd/milk, take with rice meals)"
    }
    Do not include any Markdown formatting or extra text outside the JSON.
    """

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