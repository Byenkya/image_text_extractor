import os
import cv2
import pytesseract
from pytesseract import Output
from google.cloud import vision_v1
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from textwrap3 import wrap
from typing import List
from google.cloud import vision
import os
from pandasql import sqldf
pd.options.display.float_format = '{:,.2f}'.format

# Set Tesseract OCR path
# For linux i.e ubuntu
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# For windows 
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set Google Cloud Vision API credentials
directory = os.path.abspath(__file__).replace("text_image_fucntionality.py", "")
filename = 'maracha-aa7842763068.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(directory, filename)

class TextExtractor:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.handwritten_segments: List[dict] = []

    def preprocess_image(self, img):
        # Denoise the image using a denoising filter (e.g., GaussianBlur)
        denoised_img = cv2.GaussianBlur(img, (3, 3), 0)

        # Enhance the contrast of the image (e.g., using histogram equalization)
        gray = cv2.cvtColor(denoised_img, cv2.COLOR_BGR2GRAY)
        equalized_img = cv2.equalizeHist(gray)

        return equalized_img

    def find_horizontal_lines(self):
        # Read the image
        img = cv2.imread(self.image_path)

        # Convert image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply threshold to remove background noise note: change to 0
        thresh = cv2.threshold(
            gray, 
            30, 
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]

        # Define the rectangle structure (line) to look for: width 200, height 1
        horizontal_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (200, 1)
        )

        # Find horizontal lines
        lineLocations = cv2.morphologyEx(
            thresh, 
            cv2.MORPH_OPEN, 
            horizontal_kernel, 
            iterations=1
        )

        if lineLocations.size == 0:
            print("No lines found in the image. Unable to extract segments.")
            return None

        return lineLocations

    def page_segmentation(self, img, w, df_SegmentLocations):
        # Read the image
        img = cv2.imread(img)

        # Create a copy of the image
        im2 = img.copy()

        segments = []

        for i in range(len(df_SegmentLocations)):
            # Get the starting row and height of the segment
            y = df_SegmentLocations['SegmentStart'][i]
            h = df_SegmentLocations['Height'][i]

            # Crop the segment from the image
            cropped = im2[y:y + h, 0:w]
            segments.append(cropped)

            # Display the segment
            plt.figure(figsize=(8, 8))
            plt.imshow(cropped)
            plt.title(str(i + 1))

        return segments

    def extract_text_from_img(self, segment):
        # Extract text from the image segment using Tesseract OCR
        text = pytesseract.image_to_string(segment, lang='eng')
        text = text.encode("gbk", 'ignore').decode("gbk", "ignore")
        return text

    def cloud_vision_text_extractor(self, handwritings):
        # Convert the image segment to bytes for submission to Google Cloud Vision
        _, encoded_image = cv2.imencode('.png', handwritings)
        content = encoded_image.tobytes()
        image = vision_v1.types.Image(content=content)

        # Feed the handwriting image segment to the Google Cloud Vision API
        client = vision.ImageAnnotatorClient()
        response = client.document_text_detection(image=image)

        return response

    def get_text_from_vision_response(self, response):
        texts = []
        for page in response.full_text_annotation.pages:
            for i, block in enumerate(page.blocks):
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        texts.append(word_text)

        return ' '.join(texts)

    def extract_handwritten_segments(self):
        # Step 1: Perform page segmentation to find lines between sections and break the image into segments

        lineLocations = self.find_horizontal_lines()

        if lineLocations.size == 0:
            print("No lines found in the image. Unable to extract segments.")
            return []

        df_lineLocations = pd.DataFrame(
            lineLocations.sum(axis=1), 
            dtype='object'
        ).reset_index()
        df_lineLocations.columns = ['rowLoc', 'LineLength']
        df_lineLocations['line'] = 0
        df_lineLocations.loc[df_lineLocations['LineLength'] > 100, 'line'] = 1
        df_lineLocations['cumSum'] = df_lineLocations['line'].cumsum()

        # Step 2: Extract segment locations using cumulative sum and group by cumSum
        if df_lineLocations['line'].sum() == 0:
            print("No segments found in the image. Unable to extract handwritten segments.")
            return []

        df_SegmentLocations = df_lineLocations[df_lineLocations['line'] == 0].groupby('cumSum').agg(
            SegmentOrder=('rowLoc', lambda x: x.index.min() + 1),
            SegmentStart=('rowLoc', 'min'),
            Height=('rowLoc', lambda x: x.max() - x.min())
        ).reset_index()

        img = cv2.imread(self.image_path)
        if img is None:
            print(f"Failed to read image at '{self.image_path}'. Please ensure the image file exists and can be accessed.")
            return []

        w = lineLocations.shape[1]
        segments = self.page_segmentation(self.image_path, w, df_SegmentLocations)

        handwritten_segments = []

        for segment in segments:
            # Step 3: Extract printed text from the segment
            text = self.extract_text_from_img(segment)
            
            # Step 4: Extract handwritten text using Google Cloud Vision API
            response = self.cloud_vision_text_extractor(segment)
            handwritten_text = self.get_text_from_vision_response(response)

            if handwritten_text.strip() != '':
                handwritten_segments.append({
                    'segment': segment,
                    'text': handwritten_text.strip()
                })

        return handwritten_segments

    def save_extracted_data(self, handwritten_segments, output_file):
        with open(output_file, 'w') as file:
            for i, segment_data in enumerate(handwritten_segments):
                segment_text = segment_data['text']
                wrapped_text = wrap(segment_text, 30)
                file.write(f"Segment {i+1} Handwritten Text:\n")
                file.write('\n'.join(wrapped_text))
                file.write('\n\n')

            print(f"Extracted data saved to '{output_file}'")

        return None

if __name__ == "__main__":
    # Usage example
    image_path = './test_images/AM8.jpeg'
    text_extractor = TextExtractor(image_path)
    handwritten_segments = text_extractor.extract_handwritten_segments()

    for i, segment_data in enumerate(handwritten_segments):
        segment = segment_data['segment']
        text = segment_data['text']
        
        # Create a 1x2 grid of subplots for better visualization
        fig = plt.figure(figsize=(12, 6))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])
        
        # Plot the image segment on the left
        ax0 = plt.subplot(gs[0])
        ax0.imshow(segment)
        ax0.set_title(f"Segment {i+1}")
        
        # Plot the extracted text on the right
        ax1 = plt.subplot(gs[1])
        ax1.text(0.1, 0.5, "\n".join(wrap(text, 30)), fontsize=12)
        ax1.axis('off')  # Hide the axis for the text subplot
        ax1.set_title("Extracted Text")
        
        plt.tight_layout()
        plt.show()

    output_file = './extracted_data/extracted_data.txt'
    text_extractor.save_extracted_data(handwritten_segments, output_file)
