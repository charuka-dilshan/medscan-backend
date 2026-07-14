import easyocr


reader = easyocr.Reader(["en"])


def extract_text(image_path):
    """
    Extract text from medicine/prescription image
    """

    results = reader.readtext(image_path)

    extracted_text = []

    for result in results:
        text = result[1]
        extracted_text.append(text)

    final_text = " ".join(extracted_text).strip()

    return {
        "text": final_text
    }