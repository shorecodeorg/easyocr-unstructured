
# EasyOCR Unstructured

EasyOCR Unstructured is a powerful library for Optical Character Recognition (OCR) that can extract text from PDFS, then group the text based on proximity.

It is intended for PDF files that have text that doesn't follow the left to right top to bottom standard of document writing.


## Getting Started

pip install easyocr-unstructured


import easyocr_unstructured

easyocr = EasyocrUnstructured()
result = easyocr.invoke('/path/to/your_pdf_file.pdf')

#result will be a list of lists containing strings

### Prerequisites

Python 3.12 +

### Installing

pip install easyocr-unstructured

## Usage

import easyocr_unstructured

easyocr = EasyocrUnstructured()
result = easyocr.invoke('/path/to/your_pdf_file.pdf')

## Running the tests

No tests yet

## Built With

Wing Pro
Python 3.12
numpy
easyocr
pdf2image
hashlib

## Contributing

Please do, any sensible and safe change will be added!

## Authors

Kevin Fink

## License

MIT

## Acknowledgments

