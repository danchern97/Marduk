import fitz
import cv2
import numpy as np
import os
from utils import get_text_bboxes


DATA_FOLDER = './data'
SAVE_FOLDER = "./test_bboxes"
DIFF = 5
MIN_LINES = 15


if __name__ == "__main__":
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    pdf_files = [DATA_FOLDER + '/' + filename for filename in os.listdir(DATA_FOLDER) if '.pdf' in filename]
    for filepath in pdf_files:
        print("pdf:", filepath)
        folder_name = os.path.basename(filepath) + "_folder"
        folder = os.path.join(SAVE_FOLDER, folder_name)
        os.makedirs(folder, exist_ok=True)
        doc = fitz.open(filepath)
        for i, page in enumerate(doc.pages()):
            clusters = get_text_bboxes(page)
            print("page: {}, num_clusters: {}".format(i, len(clusters)))
            matrix = fitz.Matrix(1, 1)
            page_img = page.get_pixmap(matrix = matrix)
            img_bytes = page_img.tobytes()
            img_np = np.frombuffer(img_bytes, dtype=np.uint8)
            img_cv = cv2.imdecode(img_np, flags=1)
            for cluster in clusters:
                img_cv = cv2.rectangle(img_cv, (int(cluster["left"]), int(cluster["top"])), 
                                               (int(cluster["right"]), int(cluster["bottom"])), 
                                               (0, 255, 0), 1)
            page_path = os.path.join(folder, "page_{}.jpg".format(i))
            cv2.imwrite(page_path, img_cv)
