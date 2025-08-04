from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Setup Chrome options
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

# Initialize driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.flipkart.com")

# Close login popup if it appears
try:
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'✕')]"))
    ).click()
except:
    pass

# Search term
search_term = "Car Perfumes"
search_box = driver.find_element(By.NAME, "q")
search_box.send_keys(search_term)
search_box.submit()

# Wait until results are loaded
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//div[@data-id]"))
)

products = []
page = 1
max_products = 50

# Loop through pages
while len(products) < max_products:
    print(f"Scraping page {page}...")
    cards = driver.find_elements(By.XPATH, "//div[@data-id]")

    for card in cards:
        if len(products) >= max_products:
            break
        try:
            # Try multiple possible class names for product title
            try:
                name = card.find_element(By.XPATH, ".//div[contains(@class, '_4rR01T')]").text
            except:
                try:
                    name = card.find_element(By.XPATH, ".//a[contains(@class, 's1Q9rs')]").text
                except:
                    try:
                        name = card.find_element(By.XPATH, ".//div[contains(@class, 'KzDlHZ')]").text
                    except:
                        name = ''

            try:
                price = card.find_element(By.XPATH, ".//div[contains(@class, '_30jeq3') or contains(@class, 'Nx9bqj') or contains(@class, '_4b5DiR')]").text
            except:
                price = ''

            try:
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                link = ''

            products.append({'Product Name': name, 'Price': price, 'Link': link})

        except Exception as e:
            print(f"Error scraping a card: {e}")
            continue

    # Scroll and go to next page
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        next_btn = driver.find_element(By.XPATH, "//span[contains(@class, '_1LKTO3') and text()='Next']")
        ActionChains(driver).move_to_element(next_btn).click().perform()
        page += 1
        time.sleep(3)
    except Exception as e:
        print("No more pages or next button not found:", e)
        break

print(f"\nCollected {len(products)} product links.\n")

# Now visit each product link for details
for index, product in enumerate(products, 1):
    print(f"Processing product {index}/{len(products)}")
    driver.get(product['Link'])
    time.sleep(3)

    try:
        product['Full Title'] = driver.find_element(By.XPATH, "//span[@class='B_NuCI']").text
    except:
        product['Full Title'] = ''

    try:
        product['Rating'] = driver.find_element(By.XPATH, "//div[contains(@class,'XQDdHH')]").text
    except:
        product['Rating'] = ''

    try:
        product['Number of Ratings'] = driver.find_element(By.XPATH, "//span[contains(@class,'Wphh3N')]").text
    except:
        product['Number of Ratings'] = ''

    try:
        product['Delivery Time'] = driver.find_element(By.XPATH, "//span[@class='Y8v7Fl']").text
    except:
        product['Delivery Time'] = ''

    try:
        product['Discount'] = driver.find_element(By.XPATH, "//div[contains(@class, 'UkUFwK') or contains(@class,'WW8yVX')]").text
    except:
        product['Discount'] = ''

    try:
        driver.find_element(By.XPATH, "//div[contains(text(),'This item is currently out of stock')]")
        product['Availability'] = 'Out of Stock'
    except:
        product['Availability'] = 'In Stock'

# Save data to CSV
try:
    df = pd.DataFrame(products)
    df.to_csv("flipkart_products.csv", index=False)
    print("\n✅ Data saved to 'flipkart_products.csv'")
except Exception as e:
    print("\n❌ Failed to save CSV:", e)

driver.quit()
