import time
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logging.basicConfig(filename='trading_bot.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

st.title("Plus500 Trading Bot")
st.sidebar.header("Configuration")
username = st.sidebar.text_input("Plus500 Username")
password = st.sidebar.text_input("Plus500 Password", type="password")
asset_url = st.sidebar.text_input("Asset URL", "https://www.plus500.com/en/Trading/Indices")
alert_type = st.sidebar.selectbox("Alert Type", ["Above", "Below", "Moving Average"])
alert_threshold = st.sidebar.number_input("Alert Price Threshold", min_value=0.0, value=1000.0, step=0.01)
email = st.sidebar.text_input("Alert Email Address")
email_password = st.sidebar.text_input("Email Password", type="password")
recipient_email = st.sidebar.text_input("Recipient Email Address", email)
check_interval = st.sidebar.number_input("Check Interval (seconds)", min_value=60, value=300, step=60)

start_bot = st.sidebar.button("Start Bot")
stop_bot = st.sidebar.button("Stop Bot")
driver = None
running = False
def login_to_plus500():
    driver.get('https://www.plus500.com/')
    time.sleep(3)

    try:
        login_button = driver.find_element(By.XPATH, '//a[@data-qa="header-login-button"]')
        login_button.click()
        time.sleep(2)

        username_field = driver.find_element(By.ID, 'username')
        password_field = driver.find_element(By.ID, 'password')

        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        st.success("Logged in to Plus500 successfully")
        logging.info("Logged in to Plus500 successfully")
    except Exception as e:
        st.error(f"Failed to log in to Plus500: {e}")
        logging.error(f"Failed to log in to Plus500: {e}")
        raise
def monitor_market():
    driver.get(asset_url)
    time.sleep(3)

    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        price_element = soup.select_one('.instrumentPrice span')
        if price_element:
            price_text = price_element.text
            price = float(price_text.replace(',', ''))

            st.write(f'Current price: {price}')
            logging.info(f'Current price of monitored asset: {price}')

            if (alert_type == "Above" and price > alert_threshold) or \
               (alert_type == "Below" and price < alert_threshold):
                send_email_alert(price)
        else:
            st.warning("Price element not found on the page. Check the asset URL or site structure.")
            logging.warning("Price element not found on the page. Check the asset URL or site structure.")
    except Exception as e:
        st.error(f"Failed to monitor market: {e}")
        logging.error(f"Failed to monitor market: {e}")
        raise
def send_email_alert(price):
    subject = f"Trading Bot Alert: Price {alert_type} Threshold"
    body = f"The price has crossed the threshold. Current price: {price}"
    
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, email_password)
        text = msg.as_string()
        server.sendmail(email, recipient_email, text)
        server.quit()
        st.success("Email alert sent successfully")
        logging.info("Email alert sent successfully")
    except Exception as e:
        st.error(f"Failed to send email alert: {e}")
        logging.error(f"Failed to send email alert: {e}")
def run_bot():
    global running, driver
    if running:
        st.warning("Bot is already running")
        return

    running = True

    try:
        options = Options()
        options.headless = True
        service = Service(executable_path='/path/to/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        login_to_plus500()
        while running:
            monitor_market()
            time.sleep(check_interval)
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")
    finally:
        if driver:
            driver.quit()
        running = False
if start_bot:
    run_bot()
if stop_bot:
    running = False
    st.info("Bot stopped")
    logging.info("Bot stopped")
