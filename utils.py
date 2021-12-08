#!usr/bin/python3

# pdf preprocessing
import fitz
# collect statistics on font size
from collections import Counter
import numpy as np


def determine_text_type(fonts, line, text_bbox): 
    # determine text type by intersection with fonts classification
    lineType = "other"
    for textType in fonts: # determine by font
        if len(set(fonts[textType]).intersection(set(line['fonts']))) > 0:
            lineType = textType
            break
    #  if it is out of bbox and not title - break
    if (not is_block_in_text_bbox(line, text_bbox)) and lineType != 'title': 
        lineType = "other"
    return lineType

def parse_text_block(block, text_bbox, fonts):
    textLines = []
    # first connect spans into lines
    for line in block['lines']: 
        lineText = " ".join(span['text'] for span in line['spans'])
        lineFonts = {(span['font'], span['size']) for span in line['spans']}
        textLines.append({'bbox':line['bbox'], 'text':lineText, 'fonts':list(lineFonts)})
    # next, saw lines together into paragraphs
    paragraphs = []
    prevLine = textLines[0]
    currentParagraph = {'text':prevLine['text'], 'type':determine_text_type(fonts, prevLine, text_bbox)}
    for line in textLines[1:]:
        lineType = determine_text_type(fonts, line, text_bbox)
        # if it is a new paragraph:
        left, bottom, right, top = line['bbox']
        prevLeft, prevBottom, prevRight, prevTop = prevLine['bbox']
        is_new_paragraph = (left > prevLeft)  # line breaks
        if currentParagraph['type'] != lineType or is_new_paragraph:
            paragraphs.append(currentParagraph)
            currentParagraph = {'text':line['text'], 'type':lineType}
        # if it is not a new paragraph:
        if currentParagraph['text'][-1] == '-': # line break
            currentParagraph['text'] = currentParagraph['text'][:-1] + line['text']
        else:
            currentParagraph['text'] = currentParagraph['text'] + " " + line['text']
        prevLine = line
    if len(currentParagraph['text']) > 0:
        paragraphs.append(currentParagraph)
    # determine whether a first line in the block is a new paragraph
    if len(textLines) >= 2:
        left, bottom, right, top = textLines[1]['bbox']
        prevLeft, prevBottom, prevRight, prevTop = textLines[0]['bbox']
        paragraphs[0]['isNewParagraph'] = (left > prevLeft)
    else:
        paragraphs[0]['isNewParagraph'] = True
    return paragraphs

def parse_image_block(block):
    parsedBlock = {}
    parsedBlock['contentType'] = 'image'
    parsedBlock['image'] = block['image']
    parsedBlock['width'] = block['width']
    parsedBlock['height'] = block['height']
    parsedBlock['ext'] = block['ext']
    parsedBlock['colorspace'] = block['colorspace']
    parsedBlock['bbox'] = block['bbox']
    return parsedBlock

def parse_table_block(block):
    pass

def is_block_in_text_bbox(block, text_bbox): # check whether bbox of the block is in the area of text (text_bbox)
    left, top, right, bottom = block['bbox'] # bbox of a block
    # check if in is vertically inside
    flag = (bottom <= text_bbox['bottom']) and (top >= text_bbox['top'])
    # check if left corner or right corner are the text_bbox corners
    is_in_left_column = (left >= text_bbox['left_col']['left']) and (right <= text_bbox['left_col']['right'])
    is_in_right_column = (left >= text_bbox['right_col']['left']) and (right <= text_bbox['right_col']['right'])
    flag = flag and (is_in_left_column or is_in_right_column)
    return flag

def is_first_table_block(block):
    return 'table' in block['lines'][0]['spans'][0]['text'].lower()

def filter_out_other(parsedPage): # filter out other types of garbage
    parsedPage['texts'] = [text for text in parsedPage['texts'] if text['type'] != 'other']
    return parsedPage

def parse_page(page, fonts): # parse blocks on one page
    #   
    content = page.getText('dict')
    text_bbox = get_text_bbox(page)
    #  
    images = []
    texts = []
    tables = []
    #
    table_flag = False
    #   
    for block in content['blocks']:
        if block['type'] == 1: # image
            images.extend(parse_image_block(block))
        elif block['type'] == 0: # text or table
            if table_flag: # the last block was a table
                if is_block_in_text_bbox(block, text_bbox): # now table ended, it is text
                    texts.extend(parse_text_block(block, text_bbox, fonts))
                    table_flag = False
                # else - previous table block, so do nothing
            else:
                if is_first_table_block(block): # table starts
                    table_flag = True
                else:
                    texts.extend(parse_text_block(block, text_bbox, fonts))
    return filter_out_other({'texts':texts, 'images':images, 'tables':tables})

def parse_document(filepath): # parse whole document
    doc = fitz.open(filepath)
    parsedDoc = {}
    parsedDoc['metadata'] = doc.metadata
    parsedDoc['numPages'] = doc.pageCount
    pages = []
    font_statistics = get_fontsize_statistics(doc)
    fonts = classify_fonts(font_statistics, doc)
    for page in doc.pages():
        pages.append(parse_page(page, fonts)) # parse page blocks, add to pages
    parsedDoc['content'] = join_pages(pages) # join pages
    return parsedDoc

def get_fontsize_statistics(doc):
    fontSizes = []
    for page in doc.pages():
        content = page.getText('dict')
        for block in content['blocks']:
            if block['type'] == 0:
                for line in block['lines']:
                    for span in line['spans']:
                        fontSizes.extend([
                            (span['font'], span['size']) for i in range(len(span['text'].split(' ')))
                        ])
    return Counter(fontSizes)

def make_clusters(blocks, diff=5):

    def match_cluster(bbox, cluster):
        left = bbox[0]
        right = bbox[2]
        cluster_left = cluster["bboxes"][:, 0].mean()
        cluster_right = cluster["bboxes"][:, 2].mean()
        res = (abs(left - cluster_left) < diff) and (abs(right - cluster_right) < diff)
        return res

    clusters = []
    for i, block in enumerate(blocks):
        if block["type"] != 0:
            continue
        bbox = block["bbox"]
        is_matched = False
        for cluster in clusters:
            if match_cluster(bbox, cluster):
                cluster["bboxes"] = np.vstack((cluster["bboxes"], np.array(bbox)[np.newaxis]))
                cluster["lines_count"] += len(block["lines"])
                is_matched = True
                break
        if not is_matched:
            cluster = dict()
            cluster["bboxes"] = np.array(bbox)[np.newaxis]
            cluster["lines_count"] = len(block["lines"])
            clusters.append(cluster)
    return clusters

def get_text_bboxes(page, min_lines=15, diff=5): # rewrite: get actual text bbox for 
    content = page.get_text('dict')
    clusters = make_clusters(content["blocks"], diff=diff)
    clusters = [
        cluster for cluster in clusters if cluster["lines_count"] >= min_lines
    ]
    for cluster in clusters:
        cluster["left"] = cluster["bboxes"][:, 0].min()
        cluster["right"] = cluster["bboxes"][:, 2].max()
        cluster["top"] = cluster["bboxes"][:, 1].min()
        cluster["bottom"] = cluster["bboxes"][:, 3].max()
    return clusters

def classify_fonts(font_statistics, doc):
    # rewrite: choose fonts that are plainText, title, sectionTitle, subsectionTitle, etc.
    fonts = {}
    # plain text fonts can be found by looking for text in the bounding boxes of plain text
    fonts['plainText'] = [
        ('BEAGLK+AdvPSFT-B', 7.970200061798096),
        ('BEAGLM+AdvPSFT-L', 7.970200061798096), 
        ('BEAGND+AdvPSMP13', 7.970200061798096), 
        ('BEAGNB+AdvPSFT-LI', 7.970200061798096),
        ('BEAGLP+AdvTTec369687+20', 7.970200061798096)
    ]
    # title font can be found on the first page, by it's size or by intersection with metadata['title']
    fonts['title'] = [
        ('BEAGLK+AdvPSFT-B', 16.936399459838867), 
        ('BEAGLL+AdvPSMP11', 16.936399459838867)
    ]
    #  could be found by looking for higher sizes of text in the text bbox
    fonts['sectionTitle'] = [('BEAGLK+AdvPSFT-B', 9.962599754333496)] 
    fonts['subsectionTitle'] = [
        ('BEAGLK+AdvPSFT-B', 8.468199729919434),
        ('BEAGLL+AdvPSMP11', 8.468199729919434)
    ] 
    return fonts

def join_pages(pages): 
    # rewrite: join pages: fix
    output = pages[0]
    for page in pages[1:]:
        output['images'].extend(page['images'])
        output['tables'].extend(page['tables'])
        if len(page['texts']) == 0:
            continue
        prevPageLastParagraph = output['texts'][-1]
        
        if page['texts'][0]['isNewParagraph'] or page['texts'][0]['type'] != prevPageLastParagraph['type']:
            output['texts'].extend(page['texts'])
        else:
#             print("Page: " + page['texts'][0]['text'])
#             print("Output: " + output['texts'][-1]['text'])
#             print()
            output['texts'][-1]['text'] += " " + page['texts'][0]['text']
            output['texts'].extend(page['texts'][1:])
    return output