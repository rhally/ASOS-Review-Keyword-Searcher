from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from collections import Counter
from tqdm import tqdm

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox --headless')
options.set_capability("loggingPrefs", {'performance': 'ALL'})

url_list = []
results_list = []

product_list_url = input("Enter the product list URL:\n")

cs_words = input("Enter comma-separated word(s) to search for:\n");
words_list = [str(x) for x in cs_words.split(', ')]

def get_products(product_list_url):
    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=options
    )

    wait = WebDriverWait(driver, 10)
    driver.get(product_list_url)
    while True:
        try:
            loadmore = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,"[data-auto-id='loadMoreProducts']")))
            driver.execute_script("arguments[0].click();", loadmore)
            wait.until(EC.element_to_be_clickable(loadmore))
        except Exception: break
    
    print('Loaded all products')

    print('Creating URL list...')
    for article in tqdm(wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"[data-auto-id='productTile']"))), colour='blue'):
        a = driver.find_element(By.CSS_SELECTOR, "article[id='" + article.get_attribute('id') + "']").find_element(By.CSS_SELECTOR, "a")
        url_list.append(a.get_attribute('href'))

    driver.close()
    driver.quit()


def get_review_count():
    product_url = ""

    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=options
    )

    driver.get(product_url)
 
    inner_html = WebDriverWait(driver, 25).until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@data-bind,'text: getReviewCount()')]"))).get_attribute("innerHTML")

    review_count = int(re.sub('\D', '', inner_html))

    print(review_count)

    driver.close()
    driver.quit()


def get_reviews(words_list, url_list):
    print("Iterating through URL list...")
    for item in tqdm(url_list, colour='green'):
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
        )
        driver.get(item)

        wait = WebDriverWait(driver, 25)

        while True:
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test-id='reviewsViewAll']")))
                driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "[data-test-id='reviewsViewAll']"))
                print("View all reviews button clicked")
            except TimeoutException:
                print('View all reviews button was not found, or can no longer be clicked.')
                break

        while True:
            try:
                wait.until(EC.presence_of_element_located((By.ID, "viewMoreRatings")))
                driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "viewMoreRatings"))
                print("View more ratings button clicked")
                wait.until(EC.visibility_of_element_located((By.ID, "viewMoreRatings")))
            except TimeoutException:
                print('View more ratings button was not found, or can no longer be clicked.')
                break
       
        string = ""
        article_xpath = ".//article[starts-with(@class, 'r_')]/*[not(div)]"
        reviews = driver.find_elements('xpath', article_xpath)
        for article in tqdm(reviews, colour='yellow'):
            string += article.text + " "

        c = Counter(''.join(char for char in s.lower() if char.isalpha()) 
                for s in string.split())

        count = 0
        for word in words_list:
            count += c[word]

        results_list.append([count, item])

        driver.close()
        driver.quit()

    with open('results_list.txt', 'w') as f:
        for line in results_list:
            f.write(str(line))
            f.write('\n')

    for result in sorted([(key,value) for (key,value) in results_list], reverse=True):
        print('[' + str(result[0]) + '] ' + str(result[1]))


    
get_products(product_list_url)
get_reviews(words_list, url_list)
