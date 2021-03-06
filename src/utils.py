#!usr/bin/python3

# pdf preprocessing
import fitz
# collect statistics on font size
from collections import Counter

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
                        tokens = list(filter(str.strip, span['text'].split(' ')))
                        fontSizes.extend([
                            (span['font'], span['size']) for i in range(len(tokens))
                        ])
    return Counter(fontSizes)

def get_text_bbox(page): # rewrite: get actual text bbox for 
    text_bbox = {
        'left_col':{
            'left':42,
            'right':290
        },
        'right_col':{
            'left':300,
            'right':555
        },
        'top':50,
        'bottom':710
    }
    return text_bbox

def classify_fonts(font_statistics, doc):
    # rewrite: choose fonts that are plainText, title, sectionTitle, subsectionTitle, etc.
    fonts = {}

    # plain text fonts can be found by looking for text in the bounding boxes of plain text
    font_mean = sum(font_statistics.values()) / len(font_statistics)
    fonts['plainText'] = [font for font, count in font_statistics.items() if count >= font_mean]
    # fonts['plainText'] = [
    #     ('BEAGLK+AdvPSFT-B', 7.970200061798096),
    #     ('BEAGLM+AdvPSFT-L', 7.970200061798096), 
    #     ('BEAGND+AdvPSMP13', 7.970200061798096), 
    #     ('BEAGNB+AdvPSFT-LI', 7.970200061798096),
    #     ('BEAGLP+AdvTTec369687+20', 7.970200061798096)
    # ]

    # title font can be found on the first page, by it's size or by intersection with metadata['title']
    title = doc.metadata['title']
    
    if not title:
        title = doc.get_toc()[0][1]
 
    for block in doc.get_page_text(0, 'dict')['blocks']:
        if block['type'] == 0:
            span = block['lines'][0]['spans'][0]
             
            if title.startswith(span['text']):
                break

    fonts['title'] = [(span['font'], span['size']) for line in block['lines'] for span in line['spans']]

    # fonts['title'] = [
    #     ('BEAGLK+AdvPSFT-B', 16.936399459838867), 
    #     ('BEAGLL+AdvPSMP11', 16.936399459838867)
    # ]

    #  could be found by looking for higher sizes of text in the text bbox
    fonts['sectionTitle'], fonts['subsectionTitle'] = [], []
    known_fonts = fonts['plainText'] + fonts['title']

    for page in doc:
        blocks = page.get_text('dict')['blocks']
        
        for i in range(1, len(blocks) - 1):
            if blocks[i]['type'] == 0:
                span = blocks[i]['lines'][0]['spans'][0]

                if (span['font'], span['size']) not in known_fonts:
                    prev_is_plain, next_is_plain, prev_is_section = False, False, False

                    if blocks[i - 1]['type'] == 0:
                        prev_span = blocks[i - 1]['lines'][0]['spans'][0]
                        prev_is_plain = (prev_span['font'], prev_span['size']) in fonts['plainText']
                        prev_is_section = (prev_span['font'], prev_span['size']) in fonts['sectionTitle']

                    if blocks[i + 1]['type'] == 0:
                        next_span = blocks[i + 1]['lines'][0]['spans'][0]
                        next_is_plain = (next_span['font'], next_span['size']) in fonts['plainText']
                
                    if next_is_plain and (prev_is_plain or prev_is_section):
                        
                        if prev_is_plain:
                            fonts['sectionTitle'].append((span['font'], span['size']))
                        
                        elif prev_is_section:
                            fonts['subsectionTitle'].append((span['font'], span['size']))
                        
                        known_fonts.append((span['font'], span['size']))

    # fonts['sectionTitle'] = [('BEAGLK+AdvPSFT-B', 9.962599754333496)] 
    # fonts['subsectionTitle'] = [
    #     ('BEAGLK+AdvPSFT-B', 8.468199729919434),
    #     ('BEAGLL+AdvPSMP11', 8.468199729919434)
    # ]
    
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
