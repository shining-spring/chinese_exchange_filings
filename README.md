# Chinese Exchange Filings

This is a collection of python scripts to scrape the financial filings of listed companies on Shanghai exchange (script to follow for Shenzhen exchange), convert the pdf files to txt files, parse the txt files into xml files with text split into different sections based on the template specified by the Chinese Securities Regulatory Commission. The parsing script should be applicable for filings on Shenzhen exchange as well as they should also follow the guidelines by the Chinese Securities Regulatory Commission.

List of scripts (usage examples can be found in each script):
get_ste_filings.py, the script to scrape the filings within a given time range using selenium
convert2text.py, the script to convert the downloaded pdf files into txt files using pdftotext
txt2xml.py, the script to parse the txt files into xml files
get_scrc_classification.py, the script to parse pdf files published by the csrc on the industry classifications of the listed companies
to csv files

Dependencies:
selenium, pdftotext, lxml, pandas

# 上市公司财报

这里搜集的一些python脚本可以用来抓上交所历年的财报（深交所的脚本稍后会上），并把抓下来的pdf文件转换成txt文件，以及把读取txt文件并按章节将文本存储在xml文件里面，xml文件的每个节点对应报告里面的一个章节。章节的提取是基于证监会对财报的指导意见。转换成xml这个脚本应该也适用于深交所的财报，因为他们应该都遵守同样的指导意见。

脚本列表（使用例子可以在每个相应的脚本里面找到）
get_ste_filings.py, 用selenium抓指定时间段里上交所的财报
convert2text.py, 用pdftotext将pdf文件转换成txt文件
txt2xml.py, 将txt文件转换成xml文件
get_scrc_classification.py, 可用于将证监会每年发布的上市公司行业分类结果转换成csv文件


依赖:
selenium, pdftotext, lxml, pandas
