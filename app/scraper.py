import os
import requests
import logging
import csv
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Updated headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.amazon.fr/',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Pragma': 'no-cache',
}

# Cookies extracted from the browser
cookies = {
    'aws-target-data': '%7B%22support%22%3A%221%22%7D',
    'aws-ubid-main': '947-8828354-1686536',
    'csm-hit': 'DJCEVCWK47055K85E308+s-RSTSKAC53PN3G0P20QBS|1734825495997',
    'i18n-prefs': 'EUR',
    'regStatus': 'registering',
    'session-id': '259-7299239-0150162',
    'session-id-time': '2082787201l',
    'session-token': '5hZd41n03IRDsWCrWnmzi/buTLgEYb+0egPg8j3kDjAs57o9KoHsambYQVQTm31wSWAXlyH+lSyJ6hLdyAyjKfGRLADVnQ/j8gYGyHBc5wfqj5WGz8OCBu0CRmMHqn+gcKizj1Ir0pw47Ke9nJevRSPT8wbXXR/2IImDNitCBG5ywSK+XRvCDQvZZNf8q1URxVRQoa+L1QcofJAAoJAAWWDJhNK2gDEqSSpqJc4CLTVZV9hmavaspBXBY1XAFkOSbHTL7T+AQxc0SkvmBmQVO1EpW4ynl0NUMgPguGP8u2EO5Jeu0EnE8j1kerz10M/oI0/qdvb2Lmifo0++N0+p/f4PKV+eTLnr',
    'ubid-acbfr': '260-3765963-2076313',
}

def save_image(image_url, product_title):
    try:
        logger.info(f"Downloading image from URL: {image_url}")
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        
        # Create the directory if it doesn't exist
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            logger.info(f"Created directory: {image_dir}")
        
        # Create a valid file name based on the product title
        file_name = f"{product_title[:50].replace(' ', '_').replace('/', '_')}.jpg"
        image_path = os.path.join(image_dir, file_name)
        
        # Download and save the image
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logger.info(f"Image saved successfully as {image_path}")
            return image_path
        else:
            logger.error(f"Failed to download image. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while saving the image: {e}")
        return None

def fetch_product_details(url, headers, cookies):
    try:
        logger.info(f"Fetching details for URL: {url}")
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            logger.info("Successfully fetched the product page!")
            soup = BeautifulSoup(response.text, 'lxml')

            # Extracting details
            product_details = {}
            title = soup.select_one('span#productTitle')
            product_title = title.text.strip() if title else "Not found"
            product_details['Title'] = product_title

            # Price extraction
            whole_price = soup.select_one('span.a-price-whole')
            fraction_price = soup.select_one('span.a-price-fraction')
            currency_symbol = soup.select_one('span.a-price-symbol')

            if whole_price and fraction_price and currency_symbol:
                price = f"{whole_price.text.strip()},{fraction_price.text.strip()} {currency_symbol.text.strip()}"
            else:
                price = "Not available"
            product_details['Price'] = price

            # Availability
            availability = soup.select_one('div#availability span.a-declarative span')
            product_details['Availability'] = availability.text.strip() if availability else "Not specified"

            # Ratings
            rating = soup.select_one('span.a-icon-alt')
            product_details['Rating'] = rating.text.strip() if rating else "Not rated"

            # Number of Reviews
            reviews = soup.select_one('span#acrCustomerReviewText')
            product_details['Number of Reviews'] = reviews.text.strip() if reviews else "No reviews"
            details_table = soup.select('div.a-section.a-spacing-small.a-spacing-top-small table.a-normal.a-spacing-micro')
            if details_table:
                rows = details_table[0].select('tr')
                description = []
                for row in rows:
                    key = row.select_one('td span.a-size-base.a-text-bold')
                    value = row.select_one('td span.a-size-base.po-break-word')

                    if key and value:
                        description.append(f"{key.text.strip()}: {value.text.strip()}")
                product_details['Description'] = ', '.join(description)
            else:
                product_details['Description'] = "No description available"
            # Image URL and save it
            image = soup.select_one('img#landingImage')
            image_url = image['src'] if image else None
            if image_url:
                product_details['Image'] = save_image(image_url, product_title)
            else:
                product_details['Image'] = 'No image found'

            return product_details
        else:
            logger.error(f"Failed to fetch page for URL: {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error occurred for URL: {url}: {e}")
        return None

# Function to save the details to a CSV file
def save_to_csv(all_product_details, filename='product_details.csv'):
    try:
        logger.info(f"Saving product details to {filename}...")
        csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)

        file_path = os.path.join(csv_dir, filename)

        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write headers
            writer.writerow(all_product_details[0].keys())
            # Write all product details
            for product_details in all_product_details:
                writer.writerow(product_details.values())
        logger.info(f"Product details saved to {file_path} successfully.")
    except Exception as e:
        logger.error(f"Error occurred while saving to CSV: {e}")

# Function to read URLs from links.txt
def read_links(file_path='links.txt'):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        return []

# Main execution
if __name__ == '__main__':
    links = read_links()  # Read links from links.txt
    if not links:
        logger.error("No links found in links.txt. Exiting...")
        exit()

    all_product_details = []
    for link in links:
        product_details = fetch_product_details(link, headers, cookies)
        if product_details:
            all_product_details.append(product_details)

    if all_product_details:
        save_to_csv(all_product_details)
    else:
        logger.info("No product details were fetched.")