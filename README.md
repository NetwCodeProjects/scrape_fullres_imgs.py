# scrape_fullres_imgs.py
This is a proper version that pulls from src in the html and is prepared for many edge cases like JavaScript injected <Img>.

Usage: ```python scrape_images_selenium.py https://www.example.com/gallery```

Setup: 
- ```pip install selenium beautifulsoup4 requests```
- You will need to version match ChromeDriver to Chrome browser version. ChromeDriver.exe has no install process, but requires a consistant location like C:/Documents/ChromeDriver-win64) 
    https://googlechromelabs.github.io/chrome-for-testing/
- Create PATH Environment Variable in Sys to the chromedriver-win64 folder.
- Test that chromedriver PATH is working  ```chromedriver --version```
