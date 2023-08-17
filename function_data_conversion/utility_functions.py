import re
import warnings
from pathlib import Path
from typing import List

import jsons
from docx import Document
from docx.text.paragraph import Paragraph

from data_classes import ArmyEntry

def clean_lines(lines: List[str]) -> List[str]:
    cleaned_lines = []
    for line in lines:
        text = line.strip()  # remove leading and trailing whitespace
        text = text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n") #remove weird html tags
        multiple_lines = (
            text.splitlines()
        )  # line break and page break characters are split into separate sections
        for section in multiple_lines:
            if (
                len(section) > 0
            ):  # hard coded ignore empty lines need to handle army short names aka "BH" or player names like `M`
                cleaned_lines.append(
                    " ".join(section.split())
                )  # remove weird unicode spaces \xa0
    return cleaned_lines


def Docx_to_line_list(docxFile) -> List[str]:
    # remove hyperlinks as they are treated different to paragraphs especially when that is all that is on the line.
    # This is explained https://github.com/python-openxml/python-docx/issues/85#issuecomment-917134257
    Paragraph.text = property(lambda self: GetParagraphText(self))
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for line in par:
        lines.append(line.text)
    return lines


# For avoiding hyperlinks https://github.com/python-openxml/python-docx/issues/85#issuecomment-917134257
def GetParagraphText(paragraph):
    def GetTag(element):
        return "%s:%s" % (element.prefix, re.match("{.*}(.*)", element.tag).group(1))

    text = ""
    runCount = 0
    for child in paragraph._p:
        tag = GetTag(child)
        if tag == "w:r":
            text += paragraph.runs[runCount].text
            runCount += 1
        if tag == "w:hyperlink":
            for subChild in child:
                if GetTag(subChild) == "w:r":
                    text += subChild.text
    return text


def Is_int(n) -> bool:
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()

def scrub_list(d):
    scrubbed_list = []
    for i in d:
        if isinstance(i, dict):
            i = scrub_dict(i)
        scrubbed_list.append(i)
    return scrubbed_list

def scrub_dict(d):
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = scrub_dict(v)
        if isinstance(v, list):
            v = scrub_list(v)
        if not v in (u'', None, {}, []):
            new_dict[k] = v
    return new_dict

def write_dicts_to_json(file_path: Path, data: list[dict]):
    with open(file_path, "w") as jsonFile:
        pass
    with open(file_path, "a") as jsonFile:
        for item in data:
            no_nulls = scrub_dict(item)
            if "null" in no_nulls:
                print("nulls found in json file")
                jsonFile.close
                raise ValueError(
                    f"""
                    Invalid List - null value found in
                    ArmyString: {no_nulls}
                    """
                )
            jsonFile.write(jsons.dumps(no_nulls)+"\n")

def Write_army_lists_to_json_file(
    file_path: Path, list_of_armies: List[ArmyEntry]
) -> None:
    """Takes a list of army lists and a file path and writes the list of armies in json new line delimited to the filepath

    Args:
        file_path (string): path to write new file to
        list_of_armies (list[ArmyEntry]): list of ArmyEntry objects to be written to file
    """
    # convert list of armies to a dict
    warnings.filterwarnings('ignore')
    data: list[dict] = [jsons.loads(jsons.dumps(x)) for x in list_of_armies]

    write_dicts_to_json(file_path, data)
