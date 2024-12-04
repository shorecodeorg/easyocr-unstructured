
from setuptools import setup

setup(
    name='easyocr_unstructured',
    version='1.0.10',
    author='Kevin Fink',
    author_email='kevin@shorecode.org',
    description='Parse unstructured text from PDFs',
    long_description=open('./readme.MD').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/shorecodeorg/easyocr-unstructured',  # Replace with your project URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Change if using a different license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',  # Specify your Python version requirement
)
