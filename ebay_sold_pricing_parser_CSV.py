from bs4 import BeautifulSoup
import requests
import csv


def get_search_keywords():
    """
    Prompt the user for a search item and return formatted keywords.
    :return: A list of search keywords specified by the user.
    """
    search_item = input("Input the eBay item: ").strip()
    return search_item.lower().split()


def fetch_listings(search_keywords, page_number):
    """
    Fetch listings from eBay based on search keywords and page number.
    :param search_keywords: List of keywords for the search query.
    :type search_keywords: list
    :param page_number: The page number to fetch listings from.
    :type page_number: int
    :return: A BeautifulSoup object containing the listings section.
    """
    search_query = "+".join(search_keywords)
    url = (
        f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_pgn={page_number}"
    )
    response = requests.get(url)
    doc = BeautifulSoup(response.text, "html.parser")
    return doc.find(class_="srp-results srp-list clearfix")


def parse_listing(item):
    """
    Extract title, price, date, link, and condition from a listing.
    :param item: A BeautifulSoup object representing a single listing.
    :type item: bs4.element.Tag
    :return: A tuple containing title, price, date, link, and condition.
    """
    title = item.find(class_="s-item__title").text.lower()
    price = item.find(class_="s-item__price").text
    date = item.find(class_="POSITIVE").string.replace("Sold", "").strip()
    link = item.find(class_="s-item__link")['href'].split("?")[0]
    condition = item.find(class_="s-item__subtitle").text.lower() if item.find(class_="s-item__subtitle") else "Unknown"
    return title, price, date, link, condition


def is_valid_title(title, search_keywords):
    """
    Check if the title contains all search keywords as standalone words.
    :param title: The title of the listing.
    :type title: str
    :param search_keywords: List of keywords to check in the title.
    :type search_keywords: list
    :return: True if the title contains all search keywords, False otherwise.
    """
    title_words = title.split()
    for keyword in search_keywords:
        if keyword not in title_words:
            return False
    return True


def process_price(price):
    """
    Clean and process the price string into a numeric value.
    :param price: The price string from the listing.
    :type price: str
    :return: The processed price as a numeric value.
    """
    price = price.replace("$", "").replace(",", "")
    if 'to' in price:
        price = sum(float(num) for num in price.split() if num != 'to') / 2
    return round(float(price), 2)


def main():
    """
    Main function to fetch eBay sold listings and save them to a CSV file.
    """
    search_keywords = get_search_keywords()

    with open("Sold_listings.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Title", "Price", "Date", "Link", "Condition"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write column headers to the CSV file

        for page_number in range(1, 10):
            listings_section = fetch_listings(search_keywords, page_number)
            if not listings_section:
                continue

            listings = listings_section.find_all("li", class_="s-item s-item__pl-on-bottom")
            for item in listings:
                title, price, date, link, condition = parse_listing(item)

                if is_valid_title(title, search_keywords):
                    try:
                        price_value = process_price(price)
                        # Only write listings with price between $10 and $900
                        if 10 < price_value < 900:
                            writer.writerow({
                                "Title": title,
                                "Price": f"${price_value:.2f}",
                                "Date": date,
                                "Link": link,
                                "Condition": condition
                            })
                    except ValueError:
                        continue
main()