from get_Data_From_News import GetDataFromNews
from content_analysis import ContentAnalysis

def main():
    query = "تراموا"  # پرس و جو برای جستجوی اخبار
    news_scraper = GetDataFromNews(query=query)  
    news_data = news_scraper.run()

    if not news_data.empty:
        news_data.to_excel(f"{query}.xlsx", index=False)
        print(f"News data saved to '{query}.xlsx'")
    else:
        print("No data was extracted.")


if __name__ == "__main__":
    main()
    