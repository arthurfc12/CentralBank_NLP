import os
import PyPDF2

def pdf_to_txt(pdf_path, txt_path):
    """Extracts text from a PDF and saves it to a TXT file."""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)

def batch_convert(input_folder, output_folder):
    """Converts all PDF files in input_folder to TXT files in output_folder."""
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, filename)
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(output_folder, txt_filename)

            print(f"Converting: {filename} -> {txt_filename}")
            pdf_to_txt(pdf_path, txt_path)

    print("\n✅ All PDFs converted successfully!")

if __name__ == "__main__":
    input_folder = "copom_pdfs"   # folder containing PDFs
    output_folder = "copom_txts"  # folder to save text files
    batch_convert(input_folder, output_folder)
