# -*- coding: utf-8 -*-
import scrapy
import json, ast
from scrapy.http import Request
import re
from scrapy.http import HtmlResponse
import time
import os
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
import xlsxwriter


class Newt(scrapy.Spider):
    name = 'newt'
    jsonData=[]
    start_urls=['http://www.medguideindia.com/manufacturer_test.php']
    current_path=os.getcwd()
    output_path=os.getcwd()+"/main_app/spiders/example.xlsx"
    logfile_path=os.getcwd()+"/main_app/spiders/logs/"+name+".log"
    #custon settings as described by you.
    custom_settings = {
        'LOG_ENABLED':False,
        'LOG_DATEFORMAT':'%d-%m-%y %H:%M:%S',
        'LOG_FILE':logfile_path
    }


    def parse(self,response):
        pageNo= 58
        for i in range(pageNo):
            url=f"http://www.medguideindia.com/manufacturer_test.php?nav_link=&pageNum_rr={i}&nav_link=&selectme={i}"
            print(i,"**",url)
            yield Request(url, callback= self.get_file, method="GET", errback=self.errback_httpbin, dont_filter=True)

    def get_file(self,response):
        links= response.css("td.mosttext-new > a::attr(href)").extract()
        for link in links:
            url0= "http://www.medguideindia.com/"+link
            yield Request(url0, callback= self.get_next, method="GET", errback=self.errback_httpbin, dont_filter=True)
        
    def get_next(self,response):
        links= response.css("td.mosttext > a::attr(onclick)").extract()
        for link in links:
            link= link.split("'")
            url1="http://www.medguideindia.com/"+link[1]
            yield Request(url1, callback= self.get_next1, method="GET", errback=self.errback_httpbin, dont_filter=True)

    def get_next1(self,response):
        links= response.css("td.mosttext > a::attr(onclick)").extract()
        links= links[0].split("'")
        url2="http://www.medguideindia.com/"+links[1]
        yield Request(url2, callback= self.get_next2, method="GET", errback=self.errback_httpbin, dont_filter=True)

    def get_next2(self,response):
        data= response.css(".row").extract()
        for value in data:
            rowHtml= HtmlResponse(url="my String",body=value,encoding="utf-8")
            rowValue= rowHtml.css(".mosttext::text").extract()
            lengthvalue=len(rowValue)
            print(len(rowValue))
            print(rowValue)
            print("******************************************")

            manufacturer= self.str_format(rowValue[1])
            name=self.str_format(rowValue[2])
            mtype=self.str_format(rowValue[3])
            UnitDose=self.str_format(rowValue[5])
            unit=""
            if lengthvalue==11:
                unit=self.str_format(rowValue[6])
            else:
                looplength= lengthvalue-10
                for loop in range(looplength):
                    unit+=self.str_format(rowValue[6+loop])+", "
            punit=self.str_format(rowValue[lengthvalue-3])
            tPrice=self.str_format(rowValue[lengthvalue-2])
            price=self.str_format(rowValue[lengthvalue-1])
            dataArray= [manufacturer,name,mtype,UnitDose,unit,punit,tPrice,price]
            self.jsonData.append(dataArray)
            if len(self.jsonData)>50000:
                ts= round(time.time()*1000)
                timeStamp=str(ts)
                output_path=os.getcwd()+"/main_app/spiders/xldata/med_"+timeStamp+".xlsx"
                workbook = xlsxwriter.Workbook(output_path)
                worksheet = workbook.add_worksheet()
                for row, xldata in enumerate(self.jsonData):
                    worksheet.write(row, 0, xldata[0])
                    worksheet.write(row, 1, xldata[1])
                    worksheet.write(row, 2, xldata[2])
                    worksheet.write(row, 3, xldata[3])
                    worksheet.write(row, 4, xldata[4])
                    worksheet.write(row, 5, xldata[5])
                    worksheet.write(row, 6, xldata[6])
                    worksheet.write(row, 7, xldata[7])
                workbook.close()
                self.jsonData=[]

    def str_format(self,strvalue):
        regex = re.compile(r'[\n\r\t\xa0]')
        s = regex.sub("", strvalue)
        fs= re.sub(" +"," ",s)
        outputStr= fs.strip()
        return outputStr

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

        #if isinstance(failure.value, HttpError):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        #elif isinstance(failure.value, DNSLookupError):
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        #elif isinstance(failure.value, TimeoutError):
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)



