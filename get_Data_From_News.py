import requests
from bs4 import BeautifulSoup
import pandas as pd
import jdatetime

class GetDataFromNews:
    def __init__(self, query: str):
        self.query = query
        self.url_template = (
            "https://mehrnews.com/page/search.xhtml?dt=&q={query}&"
            "a=1&df=&alltp=true&allpl=true&pi={page}&allsr=true&pageSize=50&sort=date&dr=all&allty=true"
        )

    def fetch_page(self, page: int) -> BeautifulSoup:
        url = self.url_template.format(query=self.query, page=page)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"Fetched HTML for page {page}.")
                return BeautifulSoup(response.text, "html.parser")
            else:
                print(f"Failed to fetch page {page}. Status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Request failed for page {page}: {e}")
            return None

    def get_number_pages(self) -> int:
        soup = self.fetch_page(1)
        
        if soup:
            pagination = soup.find_all("li", class_="page-item")
            if pagination:
                try:
                    last_page = pagination[-2].get_text(strip=True)
                    return int(last_page)
                except (IndexError, ValueError):
                    print("Could not determine the total number of pages.")
        return 1

    def extract_date_and_time(self,date: str) -> tuple:
        # Split the Persian date and time
        date_part, time_part = date.split(" - ")
        _, day, month_name, year = date_part.split()  # Extract parts

        # Persian month mapping
        persian_months = {
            "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4, "مرداد": 5,
            "شهریور": 6, "مهر": 7, "آبان": 8, "آذر": 9, "دی": 10,
            "بهمن": 11, "اسفند": 12
        }

        # Convert to numeric format
        day = int(day)
        month = persian_months[month_name]
        year = int(year)
        hour, minute = map(int, time_part.split(":"))
        
        # Create a jdatetime object
        jalali_date = jdatetime.date(year, month, day)
        jalali_time = jdatetime.time(hour, minute)
        
        return jalali_date, jalali_time

    def extract_article_from_link(self, link: str) -> tuple:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                article = soup.find("div", class_="item-text")
                code = soup.find("div", class_="item-code")

                article_text = article.get_text(separator="\n").strip() if article else "No article content found"
                code_text = code.find("span").text.strip() if code else "No code found"

                return article_text, code_text
        except requests.RequestException as e:
            print(f"Failed to fetch article from {link}: {e}")
        return "No article content found", "No code found"

    def extract_news_items(self, soup: BeautifulSoup,page:int) -> list:
        data = []
        if not soup:
            return data

        items = soup.find("div", class_="items")
        if not items:
            print("No news items found on this page.")
            return data

        news_items = items.find_all("li")
        for num,news in enumerate(news_items):
            try:
                title=news.find("h3").get_text().strip()
                link = "https://mehrnews.com" + news.find_next("a", href=True)["href"]
                date = news.find("time").find("a")["title"] 
                date,time = self.extract_date_and_time(date)
                article, code = self.extract_article_from_link(link)

                data.append({"Page":page,"Number":num+1,"Title": title, "Link": link, "Article": article, "Date": date,"Time":time ,"Code": code})
            except (AttributeError, TypeError) as e:
                print(f"Error processing a news item: {e} {page}")

        return data

    def run(self) -> pd.DataFrame:
        all_data = []
        total_pages = self.get_number_pages()

        for page in range(1, total_pages + 1):
            soup = self.fetch_page(page)
            if soup:
                page_data = self.extract_news_items(soup,page)
                all_data.extend(page_data)

        df = pd.DataFrame(all_data)
        df.reset_index(inplace=True)  # index را اضافه می‌کند
        df.rename(columns={"index": "ID"}, inplace=True)  # تغییر نام ستون index به ID

        return df