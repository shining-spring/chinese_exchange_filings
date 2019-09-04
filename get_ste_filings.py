"""
This script will scrape company filings from Shanghai Stock Exchange, ie.
http://www.sse.com.cn/disclosure/listedinfo/regular/
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Queue, Process
import requests
import csv
import os, sys, traceback
import datetime, time


def pick_date(driver, year, month, day, id="start_date"):
    """helper function to set date in the specified (by id) dropdown list on the webpage
    Params:
        driver: a selenium webdriver instance wherein the webpage is open
        year: int, the year of the date
        month: int, the monthe of the date
        day: int, the day of the date
        id: "start_date" or "end_date", which date to set
    """
    driver.find_element_by_xpath("//input[@id='%s']"%id).click() # first click the input element to get the view of the calendar
    rootview = [item for item in driver.find_elements_by_xpath("//div[@class='datetimepicker datetimepicker-dropdown-bottom-right dropdown-menu']") if item.is_displayed()][0]

    rootview.find_element_by_xpath("div[@class='datetimepicker-days']/table/thead/tr[1]/th[2]").click()# to get the month view
    elemen = rootview.find_element_by_xpath("div[@class='datetimepicker-months']/table/thead/tr[1]/th[2]")# to get the year
    # now choose year
    while year < int(elemen.text):
        rootview.find_element_by_xpath("div[@class='datetimepicker-months']/table/thead/tr[1]/th[1]").click()

    while year > int(elemen.text):
        rootview.find_element_by_xpath("div[@class='datetimepicker-months']/table/thead/tr[1]/th[3]").click()

    # now choose month
    rootview.find_element_by_xpath("div[@class='datetimepicker-months']/table/tbody/tr/td/span[%i]"%month).click()

    # now choose date
    days = rootview.find_elements_by_xpath("div[@class='datetimepicker-days']/table/tbody/tr/td[@class='day' or @class='day active']")
    days[day - 1].click()

def worker_savefile(toprocess, outfolder, metaqueue):
    """worker function to actually download the file
    Params:
        toprocess: Queue with incoming urls to download
        outfolder: str, output folder to save the downloaded files
        metaqueue: Queue to send the meta information for later processing
    """
    for downloadurl in iter(toprocess.get, 'STOP'):
        try:
            tmp = downloadurl.split("/")
            year = tmp[-1].split("_")[1]
            if os.path.isfile(os.path.join(outfolder, year, tmp[-1])):
                metaqueue.put((downloadurl, tmp[-1]))
                continue
            time.sleep(0.01) # otherwise the server might close the connection
            y = requests.get(downloadurl) #http://www.sse.com.cn/disclosure/listedinfo/announcement/c/2019-07-18/600203_2018_nA.pdf'

            try:
                open(os.path.join(outfolder, year, tmp[-1]), "wb").write(y.content)
            except:
                if not os.path.isdir(os.path.join(outfolder, year)):
                    os.mkdir(os.path.join(outfolder, year))
                    open(os.path.join(outfolder, year, tmp[-1]), "wb").write(y.content)
                else:
                    traceback.print_exc()
                    #print(sys.exc_info()[0])
                    raise
            metaqueue.put((downloadurl, tmp[-1]))
        except:
            print("problem downloading %s"%downloadurl)
            traceback.print_exc()
            metaqueue.put((downloadurl, None))
    metaqueue.put("STOP")


def worker_savemeta(metaqueue, outfolder, nprocesses, startdate=None, enddate=None):
    """Worker function to save the meta file
    Params:
        metaqueue: Queue with incoming meta information to save
        outfolder: output folder to save meta file
        nprocesses: number of worker processes to wait until this function finishes
        startdate: str, start date of this batch, used in naming the metafile
        enddate: str, end date of this batch, used in naming the metafile
    """
    metafile = "meta_download"
    if startdate: metafile += "_" + startdate
    if enddate: metafile += "_" + enddate
    nstops = 0
    with open(os.path.join(outfolder, metafile + ".csv"), "w") as fout:
        fieldnames = ['id', 'year', 'publish_date', 'downloadurl', 'misc', 'filepath']
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        while nstops < nprocesses:#not metaqueue.empty():
            item = metaqueue.get()
            if item == "STOP":
                nstops += 1
                continue
            downloadurl, filepath = item
            tmp = downloadurl.split("/")
            try:
                writer.writerow({"downloadurl" : downloadurl, "publish_date" : tmp[-2],
                    "id" : tmp[-1].split("_")[0], "year" : tmp[-1].split("_")[1],
                    "misc" : tmp[-1].split("_")[2][:-4], "filepath" : filepath})
            except:
                writer.writerow({"downloadurl" : downloadurl, "filepath" : filepath})

def get_file(outfolder="/home/ftang/Documents/FunProgramming/nvLDA/data",
    startdate="2000-01-01", enddate=None, overwrite=False, nprocesses=1):
    """main function to first get the download urls and pass them to the workers to
    actually download and save meta information
    Params:
        outfolder: output folder to store the files
        startdate: str, start downloading from this date
        enddate: str, end downloading to this date, if not specified, then use today
        overwrite: bool, whether to overwrite existing files, if not, will not try
        to download the files that have already been downloaded
        nprocesses: int, number of workers to spawn
    """
    if enddate is None:
        enddate = datetime.date.today().strftime("%Y-%m-%d")
    driver = webdriver.Firefox()
    url = "http://www.sse.com.cn/disclosure/listedinfo/regular/"
    toprocess = Queue()
    metaqueue = Queue()

    workers = []
    for i in range(nprocesses):
        p = Process(target=worker_savefile, args=(toprocess, outfolder, metaqueue))
        p.start()
        workers.append(p)

    driver.get(url)
    elemen = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "ht_codeinput")))

    thisstart = datetime.datetime.strptime(startdate, "%Y-%m-%d")
    thisend = thisstart + datetime.timedelta(days=30)
    if thisend > datetime.datetime(thisstart.year, 12, 31):
        thisend = datetime.datetime(thisstart.year, 12, 31)
    repeat = False
    while thisend < datetime.datetime.strptime(enddate, "%Y-%m-%d"):
        #elemen = driver.find_element_by_xpath("//input[@id='ht_codeinput']")
        tt = driver.find_elements_by_xpath("//div[@class='sse_list_1 list ']/dl/dd")[0]#driver.find_element_by_tag_name("dd")
        while True:
            pick_date(driver, thisstart.year, thisstart.month, thisstart.day, id="start_date")
            pick_date(driver, thisend.year, thisend.month, thisend.day, id="end_date")
            driver.find_element_by_xpath("//button[@id='btnQuery']").click()

            try:
                WebDriverWait(driver, 20).until(EC.staleness_of(tt))
                break
            except:
                driver.refresh()
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "ht_codeinput")))
                tt = driver.find_elements_by_xpath("//div[@class='sse_list_1 list ']/dl/dd")[0]#driver.find_element_by_tag_name("dd")

        maxpage = driver.find_elements_by_xpath("//li[@page='page']")[-2].text
        if not maxpage.isdigit(): maxpage=0
        for el in driver.find_elements_by_xpath("//div[@class='sse_list_1 list ']/dl/dd"):
            try:
                downloadurl = el.find_element_by_tag_name("a").get_attribute("href")
                toprocess.put(downloadurl)
            except:
                continue
        for i in range(1, int(maxpage) + 1):
            tt = driver.find_element_by_tag_name("dd")
            elemen = driver.find_element_by_xpath("//input[@id='ht_codeinput']")
            elemen.send_keys('%i'%i, Keys.ENTER)
            try:
                tmp = WebDriverWait(driver, 20).until(EC.staleness_of(tt))
                repeat = False
            except:
                repeat = True
                driver.refresh()
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "ht_codeinput")))
                break
            for el in driver.find_elements_by_xpath("//div[@class='sse_list_1 list ']/dl/dd"):
                downloadurl = el.find_element_by_tag_name("a").get_attribute("href")
                toprocess.put(downloadurl)
        if not repeat:
            thisstart = thisend + datetime.timedelta(days=1)
            thisend = thisstart + datetime.timedelta(days=30)
            if thisend > datetime.datetime(thisstart.year, 12, 31):
                thisend = datetime.datetime(thisstart.year, 12, 31)

    for i in range(nprocesses):
        toprocess.put("STOP")

    worker_savemeta(metaqueue, outfolder, nprocesses, startdate, enddate)
    for p in workers:
        p.join()

if __name__ == "__main__":
    get_file(outfolder="./pdf",
    overwrite=True, nprocesses=8, startdate="2017-01-01", enddate="2017-12-31")
