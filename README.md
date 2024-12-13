# HardwarePriceCharting

Required packages are listed in requirements.txt

ebay_price_logger_daily.py prompts the user for a CSV of search terms (search_terms_{Brand}_{GPU or CPU}.csv) and uses the list of search terms to scrape eBay's sold listings for historical data on prices. The prices are then written to a CSV file (Average_Price_By_Day_{Brand}_{CPU or GPU}.CSV). Scraping eBay for all the search terms takes around 20+ minutes so we have added these files to the assets folder.

dashboardapp.py uses the scraped prices and creates a GUI for easy reading and comparison of prices between hardware models. 
