import boto3
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize S3 client
s3_client = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_KEY'),
    region_name="ap-south-1" )

# Mapping of file types to their respective S3 buckets
bucket_mapping = {
    "ct": "swasth-imaging-ct",
    "mri": "swasth-imaging-mri",
    "xray": "swasth-imaging-xray",
    "ultrasound": "swasth-imaging-ultrasound",
    "kft": "swasth-lab-kft",
    "lft": "swasth-lab-lft",
    "cbp": "swasth-lab-cbp",
    "blood-glucose": "swasth-lab-blood-glucose",
    "lipid-profile": "swasth-lab-lipid-profile",
    "ecg": "swasth-cardiology-ecg",
    "eeg": "swasth-cardiology-eeg",
    "echo": "swasth-cardiology-echo",
    "histopathology": "swasth-histopathology-reports"
}

def upload_to_s3(pdf_path, pdf_type):
    """Uploads a PDF file to the respective S3 bucket based on its type."""
    
    # Validate if the type exists in our mapping
    pdf_type = pdf_type.lower()
    if pdf_type not in bucket_mapping:
        print(f"❌ Error: Unknown PDF type '{pdf_type}'. Allowed types: {list(bucket_mapping.keys())}")
        return
    
    bucket_name = bucket_mapping[pdf_type]
    
    # Get the file name
    file_name = os.path.basename(pdf_path)

    try:
        # Upload the file
        s3_client.upload_file(pdf_path, bucket_name, file_name)
        print(f"✅ Successfully uploaded '{file_name}' to bucket '{bucket_name}'")
    except Exception as e:
        print(f"❌ Error uploading file: {e}")

# Example usage
if __name__ == "__main__":
    # Display available PDF types
    print("\n📌 Available PDF Types:")
    for key in bucket_mapping.keys():
        print(f"  - {key}")

    pdf_path = input("\nEnter the PDF file path: ").strip()
    pdf_type = input("Enter the PDF type from the list above: ").strip()
    
    if os.path.exists(pdf_path):
        upload_to_s3(pdf_path, pdf_type)
    else:
        print("❌ Error: File does not exist!")
        