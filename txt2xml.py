from lxml import etree
import glob
import os
import re
import traceback

"""This script can be used to parse financial filings of listed companies in China
into sections
"""

def parse_template(infile):
    """parse template file to construct the xml structure
    """
    root = etree.Element("root")
    with open(infile, "r") as fin:
        aline = fin.readline()
        for aline in fin:
            nodename, parent = aline.strip().split(",")
            node = etree.Element("section", name=nodename.replace(" ", ""))
            if parent:
                parent = root.xpath("//section[@name='%s']"%parent.replace(" ", ""))[0]
            else:
                parent = root
            parent.append(node)
    return root

def splittext(root):
    """split the text in the root node into texts for each child of the node based
    on the section name for each child
    """
    if len(root.getchildren()) == 0 or root.text is None: return
    text = root.text.split("\n")
    matches = {}
    ptns = [re.sub("[一二三四五六七八九十]+", "[一二三四五六七八九十]+", item.get("name")) for item in root.getchildren()]
    for i, line in enumerate(text):
        line = line.replace(" ", "")
        for j, ptn in enumerate(ptns):
            if re.match(ptn, line):
                matches[j] = i
                continue
    matches = sorted(matches.items(), key=lambda s:s[1])
    root.text = ""
    last = None
    for i, match in matches[::-1]:
        root.getchildren()[i].text = "\n".join(text[match : last])
        last = match

    node = etree.Element("section", name="prefix")
    node.text = "\n".join(text[: last]) # prefix
    root.insert(0, node)

    for child in root.getchildren():
        splittext(child)

def parse_one_file(infile, outfile, template_file):
    """parse one txt file into xml based on structure specified in the template_file
    Params:
        infile: path to the txt file
        outfile: path to the output xml file
        template_file: path to the template_file
    Returns:
        etree.Element instance, with text in infile split and assigned to each child
        node based on the section title for each node.
    """
    root = parse_template(template_file)
    text = open(infile, "r").read()#.split("\n")
    root.text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', text)#text.encode("utf8").decode("utf8")
    splittext(root)
    with open(outfile, "w") as fout:
        fout.writelines(etree.tostring(root, method='xml', encoding="utf8").decode("utf8"))
    return root

def parse_one_folder(infolder, outfolder, template_file, pattern="*.txt", overwrite=False):
    """parse txt files in infolder and store the results in outfolder
    Params:
        infolder: path to the folder with txt files
        outfolder: path to store the output xml files
        template_file: path to the template file with the structures, based on guidelines_filings_csrc.pdf
        pattern: str, pattern of the files to be processed
        overwrite: bool, whether to overwrite existing files, if not, then will not
        reprocess the files that have already been processed.
    """
    filelist = glob.glob(os.path.join(infolder, pattern))
    if not os.path.isdir(outfolder):
        os.mkdir(outfolder)
    for infile in filelist:
        outfile = os.path.join(outfolder,
            os.path.splitext(os.path.split(infile)[-1])[0] + ".xml")
        if os.path.isfile(outfile) and not overwrite: continue
        try:
            parse_one_file(infile, outfile, template_file)
        except:
            print("problem processing %s"%infile)
            traceback.print_exc()
            continue

if __name__ == "__main__":
    parse_one_folder("./txt", "./xml", './template_2018.csv', "*n.txt", overwrite=True)
