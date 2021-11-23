from typing import List
from docx import Document
from data_classes import Parsers


def Docx_to_line_list(docxFile) -> List[str]:
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for i in range(len(par)):
        text = par[i].text
        if len(text) > 1:
            lines.append(text)
    return lines

def DetectParser() -> Parsers:
    #currently hardcoded to always use newrecruit
    return Parsers.NEW_RECRUIT

def Is_int(n) -> bool:
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()