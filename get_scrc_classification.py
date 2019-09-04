import pandas as pd
import pdftotext
import glob
import os
"""This script can be used to parse the pdf files published by the csrc (the Chinese
Securities Regulatory Commission) on the industry classifications of the listed companies
to csv files. This data is published on a yearly basis.
"""

def parse_one_file(infile, outfile=None):
    """parse one file
    """
    with open(infile, "rb") as f:
        pdf = pdftotext.PDF(f)
        text = "\n\n".join(pdf)

    recs = [item.split()[::-1] for item in text.split("\n")[1:]]
    df = pd.DataFrame(recs[1:])#, columns=recs[0])[recs[0][::-1]]
    df = df[df[4] != recs[0][4]]
    idx = df[3].str.isdigit() != True
    df.loc[idx, 3] = None
    df.loc[idx, 2] = None
    df.loc[idx, 4] = None
    df = df.fillna(method="ffill").drop_duplicates()

    df = df.rename(columns={i:item for i, item in enumerate(recs[0])})[recs[0][::-1]]
    if outfile:
        df.to_csv(outfile, index=False)
    return df

def parse_one_folder(infolder, classification_file=None):
    """parse everything in the infolder and combine all and save to all.csv. classification_file
    contains table of all categories 
    """
    if classification_file:
        classification = pd.read_csv(classification_file, dtype="str")
    filelist = glob.glob(os.path.join(infolder, "*.pdf"))
    res = []
    for file in filelist:
        outfile = os.path.splitext(file)[0] + ".csv"
        date = os.path.split(file)[-1][2:10]
        df = parse_one_file(file, outfile)
        df["date"] = date
        if classification is not None:
            df = pd.merge(df, classification[["大类", "门类名称", "类别名称"]], left_on="行业大类代码", right_on="大类")
        res.append(df)
    res = pd.concat(res).drop(["大类", "门类名称及代码", "行业大类名称"], axis=1)
    res.to_csv(os.path.join(infolder, "all.csv"), index=False)

if __name__ == "__main__":
    parse_one_folder("./", "./classifications.csv")
