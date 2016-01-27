#!/usr/bin/python3

import PyPDF2 as pdflib

def getPDFContent(path):
    content = ""
    # Load PDF into pyPDF
    pdf = pdflib.PdfFileReader(open(path, "rb"))
    # Iterate pages
    for i in range(0, pdf.getNumPages()):
        # Extract text from page and add to content
        content += pdf.getPage(i).extractText() + "\n"
    # Collapse whitespace
    content = " ".join(content.replace("\xa0", " ").strip().split())
    return content

print(getPDFContent("/home/oreilly/Dropbox/Lecture/DCM for phase coupling.pdf"))
