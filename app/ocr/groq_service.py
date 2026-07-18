import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def parse_prescription_text(
    prescription_text: str,
) -> Dict[str, Any]:
    """
    Convert OCR prescription text into structured JSON
    using the Groq API.
    """

    if not prescription_text or not prescription_text.strip():
        return {
            "success": False,
            "error": "Prescription text is empty.",
        }

    if not GROQ_API_KEY:
        return {
            "success": False,
            "error": "GROQ_API_KEY is missing from the .env file.",
        }

    client = Groq(
        api_key=GROQ_API_KEY
    )

    prompt = f"""
You are a medical prescription parsing assistant.

Extract the following information from the OCR text:

- medicine_name
- dosage
- frequency
- duration
- instructions

Return only valid JSON.

OCR text:
{prescription_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract prescription information "
                        "and return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content:
            return {
                "success": False,
                "error": "Groq returned an empty response.",
            }

        cleaned_content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed_data = json.loads(
            cleaned_content
        )

        return {
            "success": True,
            "data": parsed_data,
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Groq response was not valid JSON.",
        }

    except Exception as error:
        return {
            "success": False,
            "error": f"Groq processing failed: {error}",
        }