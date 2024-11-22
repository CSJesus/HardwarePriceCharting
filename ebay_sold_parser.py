from bs4 import BeautifulSoup
import requests
import statistics as stats


def get_search_keywords():
    """Prompt the user for a search item and return formatted keywords."""
    search_item = input("Input the eBay item: ").strip()
    return search_item.lower().split()


def fetch_listings(search_keywords, page_number):
    """Fetch listings from eBay based on search keywords and page number."""
    search_query = "+".join(search_keywords)
    url = (
        f"https://www.ebay.com/sch/i.html?_nkw={search_query}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1&_pgn={page_number}"
    )
    response = requests.get(url)
    doc = BeautifulSoup(response.text, "html.parser")
    return doc.find(class_="srp-results srp-list clearfix")


def parse_listing(item):
    """Extract title, price, date, and link from a listing."""
    title = item.find(class_="s-item__title").text.lower()
    price = item.find(class_="s-item__price").text
    date = item.find(class_="POSITIVE").string
    link = item.find(class_="s-item__link")['href'].split("?")[0]
    condition = item.find(class_="s-item__subtitle").text.lower()
    return title, price, date, link, condition


def is_valid_title(title, search_keywords):
    """Check if the title contains all search keywords as standalone words."""
    title_words = title.split()
    for keyword in search_keywords:
        if keyword not in title_words:
            return False
    return True


def process_price(price):
    """Clean and process the price string into a numeric value."""
    price = price.replace("$", "").replace(",", "")
    if 'to' in price:
        price = sum(float(num) for num in price.split() if num != 'to') / 2
    return round(float(price), 2)


def write_listing_to_file(file, title, price, date, link, condition):
    """Write listing details to the output file."""
    file.write(f"Title: {title}\n")
    file.write(f"Price: {price}\n")
    file.write(f"Date: {date}\n")
    file.write(f"Link: {link}\n")
    file.write(f"Condition: {condition}\n")
    file.write("---\n")


def main():
    search_keywords = get_search_keywords()
    price_list = []

    with open("Sold_listings.txt", "w", encoding="utf-8") as file:
        for page_number in range(1, 10):
            listings_section = fetch_listings(search_keywords, page_number)
            if not listings_section:
                continue

            listings = listings_section.find_all("li", class_="s-item s-item__pl-on-bottom")
            for item in listings:
                title, price, date, link, condition = parse_listing(item)

                if is_valid_title(title, search_keywords):
                    write_listing_to_file(file, title, price, date, link, condition)

                    if price:
                        try:
                            price_value = process_price(price)
                            if 900 > price_value > 10:  # Filter for prices less than $900
                                price_list.append(price_value)
                        except ValueError:
                            continue

        if price_list:
            price_list = list(set(price_list))
            file.write(f"Highest Price: ${max(price_list)}\n")
            file.write(f"Lowest Price: ${min(price_list)}\n")
            file.write(f"Average Price: ${round(sum(price_list) / len(price_list), 2)}\n")
            file.write(f"Median Price: ${round(stats.median(price_list), 2)}\n")

            print("Highest Price:", max(price_list))
            print("Lowest Price:", min(price_list))
            print("Average Price:", round(sum(price_list) / len(price_list), 2))
            print("Median Price:", round(stats.median(price_list), 2))
        else:
            print("No items found matching the criteria.")


main()