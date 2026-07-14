import easyocr
import cv2


reader = easyocr.Reader(
    ['en'],
    gpu=False,
    verbose=False
)


def preprocess_image(image_path):

    img = cv2.imread(image_path)

    # grayscale
    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # improve contrast
    thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return thresh

def clean_text(text):

    replacements = {
        "Soomg":"500mg",
        "Parace tamol":"Paracetamol",
        "Meda ic ine":"Medicine",
        "PrECRIPION":"PRESCRIPTION"
    }


    for wrong, correct in replacements.items():
        text = text.replace(
            wrong,
            correct
        )


    return text


def extract_text(image_path):

    try:

        processed = preprocess_image(image_path)

        results = reader.readtext(
            processed,
            detail=1,
            paragraph=True
        )

        texts = []

        for result in results:
            text = result[1]

            if text.strip():
                texts.append(text)

        final_text = " ".join(texts).strip()

        final_text = clean_text(final_text)

        return {
            "success": True,
            "text": final_text
        }

    except Exception as e:

        return {
            "success": False,
            "text": "",
            "error": str(e)
        }