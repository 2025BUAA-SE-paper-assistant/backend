import os
pdf_root_path = '../resource/database/papers/'


def check_pdf():
    pass

def check_all_pdfs():
    for filename in os.listdir(pdf_root_path):
        pdf_path = os.path.join(pdf_root_path, filename)
        

if __name__ == '__main__':
    check_all_pdfs()