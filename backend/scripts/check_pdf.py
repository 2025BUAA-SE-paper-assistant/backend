import os
pdf_root_path = '../resource/database/papers/'
import PyPDF2

def check_all_pdfs():
    for filename in os.listdir(pdf_root_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_root_path, filename)
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    # num_pages = len(reader.pages)
                    # print(f"{filename} 是正常的，有 {num_pages} 页")
            except Exception as e:
                print(f"{filename} 可能损坏，错误信息：{str(e)}")

if __name__ == '__main__':
    check_all_pdfs()