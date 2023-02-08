from concurrent.futures import ThreadPoolExecutor
import sys, requests, json, re, pandas as pd
from tqdm.auto import tqdm, trange
import logging as log
import time
import random

class KakaoMapPoiCollector:
    
    def __init__(self, api_key_dict, url, data_load_path, data_save_path):
        self.api_key_dict = api_key_dict
        self.url = url
        self.api_key_index = 0
        self.api_request_count = 0
        # _data_load 실행시 self.df와 self.query_list 값이 설정됨
        self._data_load(data_load_path)
        self.result_df = pd.DataFrame()
        self.data_save_path = data_save_path
        
        # self.log = log.basicConfig(filename='./log.txt', level=log.INFO)

        self.apikey = self.api_key_dict[self.api_key_index].get("key")
        
    def _set_api_key(self):
        self.api_key_index += 1
        self.apikey = self.api_key_dict[self.api_key_index].get("key")
        print("api 요청 key 변경됨")
    
    def _data_load(self, path):
        self.df = pd.read_csv(path)
        self.query_list = self.query_data_preprocessing(list(set(self.df["address"].tolist())))
        
    def query_data_preprocessing(self, query_list:list):
        _query_list = list()
        for query in query_list:
            _query_list.append(query)
            if re.search("\-\d+$",query):
                _query_list.append(re.sub("\-\d+$","",query))
                
        result_query_list = list(set(_query_list))

        print(f'중복 제거 전 {len(_query_list)}')
        print(f'중복 제거 후 {len(result_query_list)}')
        
        return result_query_list
    
    def crawler(self,query):
        crawler_result_list = list()
        for page in range(1,46):
            time.sleep(random.uniform(0.25,1))
            r = requests.get(self.url, params = {'query' : query, "page" : page, "size" : 15}, headers = {'Authorization' : 'KakaoAK ' + self.apikey })
            self.api_request_count += 1
            content = json.loads(r.content)
            # 참고 포맷
            # 'meta': {'is_end': True, 'pageable_count': 1, 'same_name': {'keyword': '', 'region': [], 'selected_region': '광주 광산구 월전동'}, 'total_count': 1}}
            if r.status_code != 200:
                # print()
                print(f"응답코드 {r.status_code} content : {json.loads(r.content)}, 요청횟수 {self.api_request_count}")
                if r.status_code == 400:
                    break 
                else:
                    self._set_api_key()
                    continue
                
            crawler_result_list.extend(json.loads(r.content).get('documents'))
            if content.get('meta').get("is_end") and page == content.get('meta').get("pageable_count"):
                break
            
        df_data = pd.DataFrame(crawler_result_list)
        # place_url
        place_url_list = self.result_df["place_url"].tolist()
        df_data = df_data[~df_data["place_url"].isin(place_url_list)]
        self.result_df = pd.concat([self.result_df,df_data],ignore_index=True)
        
        if self.api_request_count%1000 == 0:
            self.save_data_to_xlsx()

        # print(f"수집된 데이터 갯수 : {len(self.result_df.index)} api 요청 횟수 :{self.api_request_count}, 진행률 {self.query_list.index(query)/len(self.query_list):.2f}")

        if self.api_request_count%100 == 0:
            print(f"수집된 데이터 갯수 : {len(self.result_df.index)} api 요청 횟수 :{self.api_request_count}, 진행률 {self.query_list.index(query)/len(self.query_list):.2f}, duration {time.time()-self.duration}")
            # print(f"수집된 데이터 갯수 : {len(self.result_df.index)} api 요청 횟수 :{self.api_request_count}, 진행률 {self.query_list.index(query)/len(self.query_list):.2f}")
        
    # def thread_cralwer(self,result_query_list):
    def thread_cralwer(self):
        
        self.duration = time.time()
        thread_num = 15
        with ThreadPoolExecutor(max_workers=thread_num) as TP:
            TP.map(self.crawler,self.query_list)
            
        print(f"Tread map 작업 끝")
        self.save_data_to_xlsx()
        
    def save_data_to_xlsx(self): 
        # writer = pd.ExcelWriter(self.data_save_path, engine='xlsxwriter', engine_kwargs={'options':{'strings_to_urls': False}})
        # self.result_df.to_excel(writer)   
        self.result_df.to_csv(self.data_save_path, encoding="cp949")
            

if __name__ =="__main__":
    
    url = "https://dapi.kakao.com/v2/local/search/keyword.json?"
    # api_key_dict_list = [{"owner":"hj","key":"#place your api key#"},{"owner":"hg","key":"#place your api key#"},{"owner":"jw","key":"#place your api key#"}]
    api_key_dict_list = [{"owner":"jw","key":"#place your api key#"},{"owner":"hg","key":"#place your api key#"},{"owner":"hj","key":"#place your api key#"}]

    kakaoi_porcess = KakaoMapPoiCollector(url = "https://dapi.kakao.com/v2/local/search/keyword.json?",
                        data_load_path = "/mnt/workspace/poi_collector/data/jibun_concat_kakao_API_get (2).csv",
                        data_save_path = "/mnt/workspace/poi_collector/data/kakaomap20220719_result_v2.xlsx",
                        api_key_dict = api_key_dict_list
                        )
    # result_query_list = kakaoi_porcess.query_data_preprocessing()
    kakaoi_porcess.thread_cralwer()       
