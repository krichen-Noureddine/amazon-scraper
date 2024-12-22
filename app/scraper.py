import os
import requests
import logging
import csv
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Amazon product URL
product_url = 'https://www.amazon.fr/Apple-iPhone-16-Pro-128/dp/B0DGHPQJLP/ref=sr_1_1_sspa?crid=BGDBHPWCUNPV&dib=eyJ2IjoiMSJ9.3LewRmvo9sphyzsL_0IKc5Vvb-lHlfXETGlbATuapM_qVeUYGmHuvU3uMRSEQgQoBCG67Sxb96OF8nKUKfDWPlDjx1eZI50KXfbZ1hzyMFByGF81tir1vbKZZICwFR7qOcldknTnSr2bUBOcBdc7z_8MPaWQ7DMv9oSQf2o9UaAcwGcEAQuwG5woVjuILFsF7PX6PR5CA2pjBG25UH_C1KadqSs-Qnd4nja6tqLi0Gp0M4GI96tYxPzCFhYwbq0uBDL-E_aInZOokrSCVPj-jkL1gCTYOX5okfl0Z37mVt8.Gdc_wFxuRFJDxUWHbWtbRVXjy-WpUg85F00eNET-zJ0&dib_tag=se&keywords=iphone+16+pro+max&nsdOptOutParam=true&qid=1734824763&sprefix=iph%2Caps%2C382&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1'  # Replace with the actual product URL

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

# Function to fetch and parse the product page
def fetch_product_details(url, headers, cookies):
    try:
        logger.info("Sending request to fetch the product page...")
        response = requests.get(url, headers=headers, cookies=cookies)
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Successfully fetched the product page!")
            
            # Parse the HTML content using BeautifulSoup with lxml parser
            soup = BeautifulSoup(response.text, 'lxml')

            # Extracting details
            product_details = {}

            # Product Title
            title = soup.select_one('span#productTitle')
            product_details['Title'] = title.text.strip() if title else "Not found"

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

            # Product Description
            details_table = soup.select('div.a-section.a-spacing-small.a-spacing-top-small table.a-normal.a-spacing-micro')

            if details_table:
                rows = details_table[0].select('tr')
                for row in rows:
                    key = row.select_one('td span.a-size-base.a-text-bold')
                    value = row.select_one('td span.a-size-base.po-break-word')

                    if key and value:
                        product_details[key.text.strip()] = value.text.strip()

            # Extracting the product image URL
            image_url = soup.select_one('img#landingImage')
            if image_url:
                image_url = image_url['src']
                # Save the image to the images folder
                save_image(image_url)
                product_details['Image'] = image_url
            else:
                product_details['Image'] = 'No image found'

            return product_details
        else:
            logger.error(f"Failed to retrieve the page. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching the page: {e}")
    return None

# Function to save the image
def save_image(image_url):
    try:
        logger.info("Downloading image...")
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')  # One level up

        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        image_data = requests.get(image_url).content
        image_name = os.path.join(image_dir, 'product_image.jpg')

        with open(image_name, 'wb') as f:
            f.write(image_data)

        logger.info(f"Image saved as {image_name}")
    except Exception as e:
        logger.error(f"An error occurred while saving the image: {e}")

# Function to save product details to a CSV file outside the app directory
def save_to_csv(product_details, filename='product_details.csv'):
    try:
        logger.info(f"Saving product details to {filename}...")
        # Define the new directory for CSV outside the app directory
        csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')  # One level up

        # Create the directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)

        file_path = os.path.join(csv_dir, filename)
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(product_details.keys())
            # Write data
            writer.writerow(product_details.values())
        logger.info(f"Product details saved to {file_path} successfully.")
    except Exception as e:
        logger.error(f"An error occurred while saving to CSV: {e}")

# Call the function and display product details
product_details = fetch_product_details(product_url, headers, cookies)
if product_details:
    for key, value in product_details.items():
        print(f"{key}: {value}")
    save_to_csv(product_details)  # Save to CSV
else:
    print("Failed to fetch product details.")
