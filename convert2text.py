"""
This script will try to convert pdfs to text files using pdftotext
"""
import pdftotext
import glob
import os
import csv
def convert(path, outfolder, pattern="*.pdf"):
    """convert files in path with pattern and save to outfolder
    """
    filelist = glob.glob(os.path.join(path, pattern))
    meta = []
    if not os.path.isdir(outfolder):
        os.mkdir(outfolder)
    for file in filelist:
        outfile = os.path.join(outfolder, os.path.splitext(os.path.split(file)[-1])[0] + ".txt")
        if os.path.isfile(outfile):
            meta.append({"pdf" : file, "txt" : outfile})
            continue
        try:
            with open(file, "rb") as f:
                pdf = pdftotext.PDF(f)
                text = "\n\n".join(pdf)
                npages = len(pdf)

            with open(outfile, "w", encoding="utf8") as fout:
                fout.writelines(text)

            meta.append({"pdf" : file, "txt" : outfile, "npages" : npages})
        except:
            print("cannot process %s"%file)
    with open(os.path.join(outfolder, "converted.csv"), "w") as fout:
        writer = csv.DictWriter(fout, fieldnames=["pdf", "txt", "npages"])
        writer.writeheader()
        writer.writerows(meta)

if __name__ == "__main__":
    convert("./pdf", "./txt", pattern="*.pdf")
