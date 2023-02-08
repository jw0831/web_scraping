from operator import index
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import os ,sys
import time
import random
import json
import tqdm
from datetime import datetime
 
sys.path.append('/home/aift-ml/workspace/lm/KoELECTRA/finetune/KoBigBird-master/finetune/ai_analyst_api/crawler')
 
hdr = {'User-Agent' :'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'}
 
 
class Crawler:
    def crawler(self, company_name, company_code, days):
        # print("-----------------ZOOM 금융 신문기사 수집을 시작합니다. -----------------")
        page = 1 
        total_source_result = list()
        total_date_result = list()
        total_title_result = list()
        total_link_result = list()
        total_content_result = list()
        days_list = []
        stop_flag = False
        while page <= int(100):
            # print(company_code)
            url = 'https://invest.zum.com/api/domestic/stock/'+ company_code +'/news?'+'page='+str(page)+'&size=10'
            # print(url)
            time.sleep(random.uniform(4,6))
            source_code = requests.get(url, headers=hdr).text
            html = BeautifulSoup(source_code, "lxml")
            data = html.select_one('p').text
            json_data = json.loads(data)
            url_list = []
            title_list = []
            date_list = []
            source_list = []
        
            for i in json_data['newses']:
                url = i['id'] # 뉴스  링크
                title = i['title'] # 뉴스 제목
                source = i['mediaName']  # 뉴스 매체   
                date = i['registerDateTime'] # 뉴스 날짜
                date = date.replace('T',' ').replace('-','.')[:16]
                url_list.append(url) 
                title_list.append(title)
                date_list.append(date)
                source_list.append(source)
                
                
            total_source_result.extend(source_list)
            total_date_result.extend(date_list)
            total_title_result.extend(title_list)
            total_link_result.extend(url_list) 
            
            for idx, date in enumerate(total_date_result):
                date = datetime.strptime(str(date).strip(), '%Y.%m.%d %H:%M').date()
                if date not in days_list:
                    days_list.append(date)
                    first_date = days_list[0]   
                    last_date = days_list[-1]
                    # print((first_date-last_date).days)
                    
                    if int((first_date-last_date).days) > int(days): ### 날짜 이상 들어오면 스탑하고 그전 까지만 
                        remove_index = idx
                        total_source_result = total_source_result[:remove_index]
                        total_date_result = total_date_result[:remove_index]
                        total_title_result = total_title_result[:remove_index]
                        total_link_result = total_link_result[:remove_index]
                        stop_flag = True
                                      
            # print(days_list)
            first_date = days_list[0]   
            last_date = days_list[-1]
            date_tuple = (first_date, last_date)   
            # print(len(days_list))    
            if stop_flag == True:
                break
            page += 1 
            
            
        # print("크롤링 할 링크 수: ", remove_index)
        content_list = []
        if len(total_link_result) ==0:
            # print("해당 기업의 뉴스기사가 없습니다.")
            pass
        else:
            for add in total_link_result:
                time.sleep(random.uniform(4,6))
                res = requests.get(add, headers=hdr)
                soup = BeautifulSoup(res.text, 'lxml')
                content = soup.select_one('div.article_body').text
                # print(content)
                if content:
                    content = content.strip()
                else:
                    content = ""
                content = content.replace("\n"," ")
                content = re.sub(' +', ' ', content)
                content_list.append(content)

            temp_result= {"날짜" : total_date_result, "언론사" : total_source_result, "기사제목" : total_title_result, "내용" : content_list, "링크" : total_link_result} 
            temp_df = pd.DataFrame(temp_result)
            temp_df['회사명'] = company_name
            temp_df['종목코드'] = company_code
            # print("크롤링 기사 개수: ",len(temp_df))

                # content_list = [] 
                # for link in links: 
                #     add = 'https://finance.naver.com' + link.find('a')['href']
                #     link_result.append(add)
                #     res = requests.get(add)
                #     time.sleep(4)
                #     soup = BeautifulSoup(res.text, 'lxml')6
                #     content = soup.select_one('#news_read')
                #     content = content.text.strip()
                #     content_list.append(content)
            df_result = temp_df
            # print("----------------- ZOOM 투자 신문기사 수집을 완료하였습니다. -----------------")
            # print('./result/0714/crwaling_' + str(company_name) + '.xlsx')
            # df_result.to_excel('./result/crwaling_' + str(company_name) + '.xlsx', encoding='utf-8') 
        return df_result, date_tuple

    
        # # 변수들 합쳐서 해당 디렉토리에 csv파일로 저장하기 
        # print(page)
        # result= {"날짜" : total_date_result, "언론사" : total_source_result, "기사제목" : total_title_result,"내용":total_content_result, "링크" : total_link_result} 
        # df_result = pd.DataFrame(result)
        
        # print("다운 받고 있습니다------")
        # df_result.to_excel('./result/crwaling_' + str(company_name) + '.xlsx', encoding='utf-8') 
                
    
    # 종목 리스트 파일 열기  
    # 회사명을 종목코드로 변환 
            
    def convert_to_code(self, company, days):
        data = pd.read_csv('/home/aift-ml/workspace/lm/KoELECTRA/finetune/KoBigBird-master/finetune/ai_analyst_api/crawler/resource/company_list.txt', dtype=str, sep='\t')   # 종목코드 추출 
        company_name = data['회사명']
        keys = [i for i in company_name]    #데이터프레임에서 리스트로 바꾸기 
    
        company_code = data['종목코드']
        values = [j for j in company_code]
        values_re = []
        for v in values:
            if len(str(v)) == 6:
                values_re.append(v)
            elif len(str(v)) == 5:
                v = '0'+ str(v)
                values_re.append(v)
            elif len(str(v)) == 4:
                v = '00'+ str(v)
                values_re.append(v)               
            elif len(str(v)) == 3:
                v = '000'+ str(v)
                values_re.append(v)                 

        dict_result = dict(zip(keys, values_re))  # 딕셔너리 형태로 회사이름과 종목코드 묶기 
        pattern = '[a-zA-Z가-힣]+' 
        
        if bool(re.match(pattern, company)) == True:         # Input에 이름으로 넣었을 때  
            company_code = dict_result.get(str(company))
            company_name = company
            # print(company_name,"     ",company_code)
            result = self.crawler(company_name,company_code, days)
    
        else:                                                # Input에 종목코드로 넣었을 때       
            company_code = str(company)   
            company_name = company
            # print(company_name,"     ",company_code)
            result = self.crawler(company_name ,company_code, days)
            
        return result