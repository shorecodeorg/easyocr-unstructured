#kevin fink
#kevin@shorecode.org
#Wed Dec  4 01:42:15 PM +07 2024
#easyocr_unstructured.py

import numpy as np
import time
import easyocr
import pdf2image
import hashlib
import json
import os


class EasyocrUnstructured:
    def __init__(self):        
        # directory where files are saved to prevent hte slow process of scanning hte pdfs if possible
        self.output_dir = os.path.join('tmp', 'easyocr_unstructured')
        
        if not os.path.exists(self.output_dir):
            new_dir = '.'
            for entry in os.path.split(self.output_dir):                
                new_dir = os.path.join(new_dir, entry)
                if not os.path.exists(new_dir):
                    os.mkdir(new_dir)
        
        # Delete parsed PDF json files older than 7 days in output_dir
        self.delete_old_files(self.output_dir, days=7)        

    def delete_old_files(self, directory, days):
        """
        Delete files in the specified directory that are older than a specified number of days.
    
        This method iterates through all files in the given directory and checks their last modified 
        time. If a file's last modified time is older than the specified number of days, the file 
        will be deleted.
    
        Parameters:
        directory (str): The path to the directory where files will be checked and potentially deleted.
        days (int): The age threshold in days. Files older than this threshold will be deleted.
    
        Returns:
        None: This method does not return any value. It performs file deletions as a side effect.
    
        Example:
        >>> self.delete_old_files('/path/to/directory', 7)
        This will delete all files in '/path/to/directory' that are older than 7 days.
        """        
        # Get the current time
        now = time.time()
        # Calculate the threshold time
        threshold = now - (days * 86400)  # 86400 seconds in a day

        # Iterate through the files in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                # Get the last modified time
                file_mod_time = os.path.getmtime(file_path)
                # Delete the file if it's older than the threshold
                if file_mod_time < threshold:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_path}")  # Optional: log the deletion

    
    def get_new_entry(self, entry):
        """
        Convert an entry into a new bounding box format.
    
        This function takes an entry consisting of bounding box coordinates, 
        text, and probability, and returns a modified bounding box that includes 
        the text as the last element.
    
        Args:
            entry (tuple): A tuple containing the bounding box, text, and probability.
    
        Returns:
            list: A list containing the modified bounding box with the text appended.
        """
        (bbox, text, prob) = entry
        bbox = [[int(coord) for coord in point] for point in bbox]
        bbox.append(text)
        return bbox
    
    def scan_pdf(self, pdf_path):
        """Scan a PDF file and extract text from its pages using the EasyOCR library.
    
        Args:
            pdf_path (str): The path to the PDF file to be scanned.
    
        Returns:
            list: A list of bounding boxes and corresponding text extracted from the PDF.
                  Each entry in the list is a list containing the bounding box coordinates
                  followed by the extracted text.
        """    
        reader = easyocr.Reader(['en'])  # Specify the language(s) you want to use
        images = pdf2image.convert_from_path(pdf_path)
        results = []
        for image in images:
            detections = reader.readtext(np.array(image))
            for entry in detections:
                results.append(self.get_new_entry(entry))
        return results
    
    def add_new_entry(self, current_group, entries_processed, bbox, entries, entry, i, last_text):
        """
        Add a new entry to the current group if the text is different from the last entry.
    
        This function appends the current entry to the current group and 
        updates the processed entries list. It also keeps track of the 
        last bounding box for future proximity checks.
    
        Args:
            current_group (list): The list of currently grouped entries.
            entries_processed (list): The list of entries that have been processed.
            bbox (list): The bounding box coordinates of the current entry.
            entries (list): The original list of entries.
            entry (tuple): The current entry being processed.
            i (int): The index of the current entry in the original list.
            last_text (str): The text of the last processed entry.
    
        Returns:
            tuple: A tuple containing:
                - current_group (list): The updated list of currently grouped entries.
                - entries_processed (list): The updated list of processed entries.
                - last_bbox (list): The bounding box of the last entry added to the group.
        """
        if not entry[4] == last_text:        
            current_group.append(entries[i])
        entries_processed.append(entry)
        last_bbox = bbox
        return current_group, entries_processed, last_bbox
    
    def group_entries(self, entries, proximity_threshold):
        """
        Group text entries based on proximity.
    
        This function iterates through a list of entries and groups them 
        based on their bounding box proximity to each other. Entries that 
        are close enough (within the specified threshold) are grouped together.
    
        Args:
            entries (list): A list of entries, where each entry is expected 
                to contain bounding box coordinates and text.
            proximity_threshold (int): The distance threshold for grouping 
                entries based on their bounding boxes.
    
        Returns:
            tuple: A tuple containing:
                - grouped_results (list): A list of groups, where each group 
                  is a list of entries that are close to each other.
                - entries_processed (list): A list of entries that have been 
                  processed during the grouping.
        """
        grouped_results = []
        current_group = []
        last_bbox = None
        last_line = None
        entries_processed = []
        last_text = None
    
        for i, entry in enumerate(entries):
            bbox = entry[:4]
    
            if last_bbox is None:
                current_group, entries_processed, last_bbox = self.add_new_entry(current_group,
                                                                            entries_processed, bbox, entries, entry, i, last_text)
                last_text = entry[4]
                last_line = bbox
                # initialize last miss for compat
                last_miss = bbox
                continue
            # Check if the current entry is close to the last entry
            if (bbox[0][0] <= last_bbox[1][0] + proximity_threshold and  # Check x proximity
                bbox[0][1] <= last_bbox[2][1] + proximity_threshold):                
                current_group, entries_processed, last_bbox = self.add_new_entry(current_group,
                                                                            entries_processed, bbox, entries, entry, i, last_text)
                last_text = entry[4]
                continue
    
            elif (bbox[0][1] <= last_line[0][1] + proximity_threshold and 
                  bbox[0][0] <= last_line[0][0] + proximity_threshold):
                current_group, entries_processed, last_bbox = self.add_new_entry(current_group,
                                                                            entries_processed, bbox, entries, entry, i, last_text)
                last_line = bbox
                # move last_miss to next line for compat
                last_miss = bbox
                last_text = entry[4]
                continue
    
            elif bbox[0][1] != last_miss[0][1]:
                grouped_results.append(current_group)
                break
            else:
                last_miss = bbox
        return grouped_results, entries_processed
    
    def process_entries(self, entries, proximity_in_pixels):
        """Group text entries based on their proximity to each other.
        
            Args:
                entries (list): A list of entries, where each entry is a list containing
                    a list of 4 2 dimensional bounding box coordinates and extracted text.
                proximity_threshold (int): The threshold distance (in pixels) to consider
                                           entries as being in proximity to each other.
        
            Returns:
                list: A list of grouped entries, where each group is a list of strings
                      that are close to each other based on the specified proximity threshold.
            """    
        entries.sort(key=lambda x: (x[0][1], x[0][0]))
    
        grouped_results, entries_processed = self.group_entries(entries, proximity_in_pixels)
                    
        for entry in entries_processed:
            entries.remove(entry)
        
        if len(entries) > 0:
            more_entries = self.process_entries(entries, proximity_in_pixels)
            grouped_results.extend(more_entries)
        if len(grouped_results) == 0:
            grouped_results.append(list())
        
        return grouped_results
    
    def pdf_to_json(self, pdf_fp, output_fp):
        """
            Convert the contents of a PDF file to a JSON format.
        
            This function scans the PDF file specified by the file path and 
            saves a list of the coordinates and text for each entry in a JSON file.
        
            Args:
                pdf_fp (str): The file path to the PDF file to be scanned.
        
            Returns:
                list: A list of entries extracted from the PDF.
            """    
        entries = self.scan_pdf(pdf_fp)
        with open(output_fp, 'w') as f:
            json.dump(entries, f)
        return entries
    
    def get_hash(self, pdf_fp):
        """
            Generate a SHA-1 hash for the specified PDF file.
        
            This function reads the PDF file in binary mode and computes its 
            SHA-1 hash to create a unique identifier for the file.
        
            Args:
                pdf_fp (str): The file path to the PDF file.
        
            Returns:
                str: The hexadecimal representation of the SHA-1 hash of the file.
            """    
        hash_func = hashlib.sha1()
        with open(pdf_fp, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        hash_value = hash_func.hexdigest()
        return hash_value
    
    def invoke(self, pdf_fp, proximity_in_pixels=20):
        """
            Process a PDF file and group text entries by proximity.
        
            This function generates a unique output filename based on the 
            hash of the PDF file. If the output file already exists, it 
            loads the entries from the existing file; otherwise, it scans 
            the PDF and creates a new JSON file. The entries are then 
            grouped by proximity and filtered to keep only the text.
        
            Args:
                pdf_fp (str): The file path to the PDF file to be processed.
                proximity_in_pixels (int, optional): The proximity threshold 
                    for grouping text entries. Defaults to 20.
        
            Returns:
                list: A list of text entries grouped by proximity.
            """    
        #Add hash to filename to ensure it is unique
        hash_value = self.get_hash(pdf_fp)
        #Output to data/output as specified in eut_filepaths.
        #This will reduce processing time drastically if the same file is processed more than once
        output_fp = os.path.join(self.output_dir, os.path.split(hash_value+os.path.splitext(pdf_fp)[0]+'.txt')[-1])
        if not os.path.exists(output_fp):
            #Scan the pdf and create a json file with location of text and actual text
            entries = self.pdf_to_json(pdf_fp, output_fp)
        else:
            with open(output_fp, 'r') as f:
                try:                
                    entries = json.load(f)
                except:
                    entries = self.pdf_to_json(pdf_fp, output_fp)
        # group entries by proximity
        result =  self.process_entries(entries, proximity_in_pixels)
        #Filter result to only keep text, remove coordinates
        result = [list(map(lambda x: x[4], entry)) for entry in result]
        return result


if __name__ == '__main__':
    import sys
    sys.exit(0)
