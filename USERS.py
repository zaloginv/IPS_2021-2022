# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 13:18:28 2022

@author: zaloginv
"""

import time
import os
import random
import numpy as np
import simpy
import requests
from fake_useragent import UserAgent
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ПРОСМОТР URL АДРЕСОВ САЙТА
def url_seeker():
    path = '//KOMPUTER\site\infobeast'
    url_list = []
    # путь к сайту на сервере
    
    for root, dirs, files in os.walk(path):
        for file in files:
            url = os.path.join(root,file) # пишем полный путь
            url_list.append((url.replace(path,'')).replace('\\','/')) # отрезаем кусок пути
            
    return url_list



# СОЗДАНИЕ СПИСКОВ С ПОРТАМИ
class ip_make( object ):

    def __init__( self, number, num_bad_sqli, num_bad_dos ):
        self.number = number # общее число ip
        self.num_bad_sqli = num_bad_sqli # число ip, с которых идёт атака sqli
        self.num_bad_dos = num_bad_dos # число ip, с которых идёт dos атака
        
        self.ips_good = []
        self.ips_bad_sqli = []
        self.ips_bad_dos = []

        with open('E:/Tor Browser/Tor/torrc','r') as ports:
            lines = ports.readlines()
            for i in range( self.number ):
                self.ips_good.append( ( lines[ i ][ -5: ] ).replace('\n','') ) # формируем общую строчку портов, убирая по пути символ новой строки
            
            self.ips_bad_sqli.extend( self.ips_good[ 0:self.num_bad_sqli ] ) # формируем список с портов, с которых идёт атака sqli
            del self.ips_good[ 0:self.num_bad_sqli ] # удаляем скопированные портов из общего списка
            self.ips_bad_dos.extend( self.ips_good[ 0:self.num_bad_dos ] ) # формируем список с ip, с которых идёт dos атака
            del self.ips_good[ 0:self.num_bad_dos ]  # удаляем скопированные портов из общего списка
        
        
        

# ДЕЙСТВИЯ ПОРЯДОЧНОГО ПОЛЬЗОВАТЕЛЯ
class good_client( object ):
    global server
    
    def __init__( self, env, ip, rng ):
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.env = env
        self.action = env.process(self.work()) # каждый раз при вызове класса запускает новый процесс
        self.rng = rng
        self.session = requests.Session() # создаем http-сеанс
        self.proxy = ip # назначем прокси
        self.session.proxies =  {'http':  f'socks5://127.0.0.1:{self.proxy}', 'https': f'socks5://127.0.0.1:{self.proxy}'} # МЕТОД С ПРОКСИ
        # self.session.proxies =  {'http':  'socks5://127.0.0.1:9060', 'https': 'socks5://127.0.0.1:9060'} # проверка одного порта

        
        
    def timing ( self ):
        return self.rng.uniform( 30, 45 ) # время ожидания до следующей атаки
        
    def url ( self ):
        return server.main_url + random.choice( server.urls ) # выбор ссылки
        
    def work( self ):
        while True:
            try:              
               # self.retry = Retry(connect=3, backoff_factor=0.5)
               # self.adapter = HTTPAdapter(max_retries=self.retry)
               # self.session.mount('http://', self.adapter)
               # self.session.mount('https://', self.adapter)
                self.session.get (( self.url() ), headers=self.headers) # формируем запрос к случайной из существующих страниц
                yield self.env.timeout( self.timing () )
            except requests.exceptions.ProxyError as e:
                print (f'Ошибка === {e}\nПрокси === {self.proxy}\n\n')
                continue
            except requests.exceptions.ConnectionError:
                continue
            
            

# ДЕЙСТВИЯ АТАКУЮЩЕГО, КОТОРЫЙ ИСПОЛЬЗУЕТ SQLI
class bad_client_sqli( good_client ):
    def url ( self ):
        return server.main_url + random.choice( server.urls ) + random.choice( server.sqli ) # строчка, содержащая SQL инъекцию


# ДЕЙСТВИЯ АТАКУЮЩЕГО, КОТОРЫЙ ИСПОЛЬЗУЕТ DOS
class bad_client_dos( good_client ):
    def timing ( self ):
        return self.rng.uniform( 3, 7 ) # время ожидания до следующей атаки


# ХРАНИЛИЩЕ ПЕРЕМЕННЫХ ВРОДЕ ССЫЛОК
class server:
    urls = url_seeker()
    main_url = 'https://infobeast.pagekite.me' # МЕТОД С ПРОКСИ
    # main_url = 'http://infobeast/site/infobeast' # МЕТОД БЕЗ ПРОКСИ
    # sqli = '//KOMPUTER\site\infobeast' # МЕТОД С ПРОКСИ содержит пустые файлы с именами в виде атак SQL (иначе ошибка выдается с сайта pagekite, то есть, в логах записи нет)
    sqli = [
        ' SELECT ',' OR 1 = 1'," 0; 'AND ",'= '
        ]



def main():

    rng = np.random.default_rng( 0 ) # генератор случайных чисел
    ips = ip_make(5,3,1) # первое число - общее количество ip (после обработки - "хороших"), второе - атаки sqli, третье - dos
    env = simpy.rt.RealtimeEnvironment(strict=False) # моделирование процессов по таймеру
    
    
# ФОРМИРОВАНИЕ ВСЕХ КЛАССОВ ПОЛЬЗОВАТЕЛЕЙ: "ХОРОШИХ", SQLI, DOS    
    for i in range(len( ips.ips_good )):
        good_client( env, ips.ips_good[i], rng )
        time.sleep(3)
    
    for i in range(len( ips.ips_bad_sqli )):
        bad_client_sqli( env, ips.ips_bad_sqli[i], rng )
        time.sleep(3)
    
    for i in range(len( ips.ips_bad_dos )):
       bad_client_dos( env, ips.ips_bad_dos[i], rng )
       time.sleep(3)
        
    env.run() # запуск "события", то есть, активация всех сформированных классов


if __name__ == '__main__':
    main()
