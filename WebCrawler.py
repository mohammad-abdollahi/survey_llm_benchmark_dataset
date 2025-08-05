import bs4
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import re
import json
from selenium import webdriver
import random
from datetime import datetime
from urllib.parse import quote

# Initialize WebDriver
driver = webdriver.Chrome()

# Helper Functions
def loadtxt():
    return [line.strip() for line in open("query.txt", "r")]

def jsonWriter(data, filename):
    with open(f'{filename}.json', 'a') as f:
        json.dump(data, f, ensure_ascii=False)

def newWriter(row, filename):
    with open(f'{filename}.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def randomize_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    return {'User-Agent': random.choice(user_agents)}

def handle_cookie_consent():
    try:
        cookie_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'Agree') or contains(., 'OK')]"))
        )
        cookie_btn.click()
        time.sleep(2)
    except TimeoutException:
        pass

def is_recent_publication(year_text):
    try:
        year = int(re.search(r'\d{4}', year_text).group())
        return year >= 2020
    except (AttributeError, ValueError):
        return False

# Scraping Functions
def google_scholar_scraper(query, start=0):
    base_url = f"https://scholar.google.com/scholar?start={start}&q={query}&hl=en&as_sdt=0,5&as_ylo=2020"
    driver.get(base_url)
    if start == 0:
        time.sleep(30)
    else:
        time.sleep(random.uniform(2,4))
    
    try:
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "gs_ri"))
        )
        
        papers = []
        for result in results:
            try:
                title = result.find_element(By.TAG_NAME, 'h3').text
                link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                year_text = result.find_element(By.CLASS_NAME, 'gs_a').text
                
                if is_recent_publication(year_text):
                    papers.append([title, link, year_text])
            except:
                continue
        
        for paper in papers:
            newWriter(paper, 'GoogleScholarPapers')
        
        return len(papers)

    except TimeoutException:
        print("No results found or page didn't load")
        return 0

def parse_ieee(keyword, page=0):
    url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={keyword}&pageNumber={page}&ranges=2020_{datetime.now().year}_Year"
    driver.get(url)
    time.sleep(3)
    
    papers = []
    try:
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".List-results-items"))
        )
        
        for item in results:
            try:
                title = item.find_element(By.CSS_SELECTOR, "h3 a").text
                year_text = item.find_element(By.XPATH, ".//*[contains(text(), 'Year:')]").text
                
                if is_recent_publication(year_text):
                    papers.append([title, f"IEEE {year_text}"])
            except:
                continue
        
        for paper in papers:
            newWriter(paper, 'IEEEPapers')
        
        return len(papers)
    
    except TimeoutException:
        print("No IEEE results found")
        return 0

def parse_science_direct(keyword, offset=0):
    url = f'https://www.sciencedirect.com/search?date=2020-2025&tak={keyword}&offset={offset}'
    driver.get(url)
    time.sleep(3)
    handle_cookie_consent()

    papers = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "result-item-container"))
        )
        
        results = driver.find_elements(By.CLASS_NAME, "result-item-container")
        for item in results:
            try:
                title_element = item.find_element(By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'a')
                title = title_element.text
                link = title_element.get_attribute('href')
                papers.append([title, link])
            except Exception as e:
                print(f"Skipping item due to error: {e}")
                continue
        
        for paper in papers:
            newWriter(paper, 'ScienceDirectPapers')
        
        return len(papers)
    
    except TimeoutException:
        print("No ScienceDirect results found")
        return 0

def parse_acm(query, page):
    url = f"https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&expand=dl&AfterYear=2020&TITLE={query}&pageSize=20&startPage={page-1}"
    response = requests.get(url, headers=randomize_user_agent())
    soup = BeautifulSoup(response.text, 'html.parser')
    
    papers = []
    for item in soup.select('.issue-item__title'):
        try:
            title = item.text.strip()
            link = "https://dl.acm.org" + item.find('a')['href']
            year_text = item.find_next(class_='bookPubDate').text
            
            if is_recent_publication(year_text):
                papers.append([title, link, year_text])
        except:
            continue
    
    for paper in papers:
        newWriter(paper, 'ACMPapers')
    
    print(f'ACM: {len(papers)}')
    return len(papers)

# Main Execution
def main():
    queries = [
        'Benchmark+Dataset+Code+Generation+LLM',
        'Benchmark+Dataset+Code+Summarization+LLM',
        'Benchmark+Dataset+Code+Test+Cases+Generation+LLM',
        'Benchmark+Dataset+Patch+Generation+LLM',
        'Benchmark+Dataset+Code+Optimization+LLM',
        'Benchmark+Dataset+Code+Translation+LLM',
        'Benchmark+Dataset+Program+Repair+LLM',
        'Benchmark+Dataset+Requirement+Generation+LLM',
        'Benchmark+Dataset+Software+Development+LLM',
        'Benchmark+Dataset+Software+Engineering+LLM',
        'Benchmark+Dataset+Code+Review+LLM',
        'Benchmark+Dataset+Code+Generation+Large+Language+Model',
        'Benchmark+Dataset+Code+Summarization+Large+Language+Model',
        'Benchmark+Dataset+Code+Test+Cases+Generation+Large+Language+Model',
        'Benchmark+Dataset+Patch+Generation+Large+Language+Model',
        'Benchmark+Dataset+Code+Optimization+Large+Language+Model',
        'Benchmark+Dataset+Code+Translation+Large+Language+Model',
        'Benchmark+Dataset+Program+Repair+Large+Language+Model',
        'Benchmark+Dataset+Requirement+Generation+Large+Language+Model',
        'Benchmark+Dataset+Software+Development+Large+Language+Model',
        'Benchmark+Dataset+Software+Engineering+Large+Language+Model',
        'Benchmark+Dataset+Code+Review+Large+Language+Model'
    ]
    
    for query in queries:
        print(f"Processing: {query}")
        
        # Google Scholar
        count_total = 0
        for page in range(0, 6):
            count = google_scholar_scraper(query, start=page*10)
            count_total += count
            if count == 0: 
                print(f'Google Scholar papers: {count_total}')
                break
            if page == 5:
                print(f'Google Scholar papers: {count_total}')
        
        # IEEE
        count_total = 0
        for page in range(0, 20):
            count = parse_ieee(query, page)
            count_total += count
            if count == 0: 
                print(f'IEEE papers: {count_total}')
                break

        # ScienceDirect
        count_total = 0
        for offset in range(0, 250, 25):
            count = parse_science_direct(query, offset)
            count_total += count
            if count == 0:  
                print(f'ScienceDirect papers: {count_total}') 
                break
        
        # ACM
        count_total = 0
        for page in range(1, 6):
            count = parse_acm(query, page)
            count_total += count
            if count == 0: 
                print(f'ACM papers: {count_total}')
                break
            if page == 5:
                print(f'ACM papers: {count_total}')
    
    driver.quit()

if __name__ == '__main__':
    main()