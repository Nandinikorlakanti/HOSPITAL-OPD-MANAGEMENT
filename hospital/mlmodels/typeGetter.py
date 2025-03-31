import re
from docling.document_converter import DocumentConverter
from openai import OpenAI

def getFileType(source):
    
    print('starting the getter')
    print('starting the getter',source)
    converter = DocumentConverter()
    result = converter.convert(source.path)
    extracted_text = result.document.export_to_markdown()

    base_url = "https://api.novita.ai/v3/openai"
    api_key = "sk_zvO6hX67mq-VMrtVCCPOvXF8xmQSzKa3CHql_G6VuOc"  # Replace with your actual API key
    model = "deepseek/deepseek-r1-turbo"

    client = OpenAI(
    base_url=base_url,
    api_key=api_key,
    )

    document_types = [
    "ct", "mri", "xray", "ultrasound", "kft", "lft", "cbp", 
    "bloodglucose", "lipidprofile", "ecg", "eeg", "echo", "histopathologyreport"
]

    prompt = f"""
        You are an expert in medical document classification. Your task is to analyze the following text extracted from a medical report and identify its type from the list below. 
        Only respond with the exact document type from the list. Do not include any additional explanation or text. Use proper common sense,if you cannot say the type say "Unknown". 
        
        Document Types: {", ".join(document_types)}
        
        Document Text:
        {extracted_text}
        
        Document Type:
        """
        
    stream = False  # Set to True if you want streaming response
    max_tokens = 1000
    response_format = { "type": "text" }

    chat_completion_res = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=stream,
        extra_body={
            "max_tokens": max_tokens,
            "response_format": response_format
        }
    )

    # Extract the response
    if stream:
        response_text = ""
        for chunk in chat_completion_res:
            response_text += chunk.choices[0].delta.content or ""
    else:
        response_text = chat_completion_res.choices[0].message.content

    # Use regex to extract only the document type (e.g., "cbp")
    document_type_match = re.search(r"\b(" + "|".join(document_types) + r")\b", response_text, re.IGNORECASE)
    if document_type_match:
        print(document_type_match.group(0).lower())
        return document_type_match.group(0).lower()#. Print the matched document type in lowercase
    else:
        print("Unknown")  # Fallback if no document type is found
