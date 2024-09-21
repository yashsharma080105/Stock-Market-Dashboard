import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import openai

# Set up the page
st.title('Stock Dashboard')

# Sidebar for ticker, start, and end dates
ticker = st.sidebar.text_input('Ticker')
start_date = st.sidebar.date_input('Start Date')
end_date = st.sidebar.date_input('End Date')

# Chat in sidebar
with st.sidebar:
    messages = st.container()
    if prompt := st.chat_input("Say something"):
        messages.chat_message("user").write(prompt)
        messages.chat_message("assistant").write(f"Echo: {prompt}")

# Fetch and display stock data
data = yf.download(ticker, start=start_date, end=end_date)
fig = px.line(data, x=data.index, y=data['Adj Close'], title=ticker)
st.plotly_chart(fig)

# Create tabs for Pricing Data, Fundamental Data, News, and Technical Analysis
pricing_data, fundamental_data, news, tech_indicator = st.tabs(
    ["Pricing Data", "Fundamental Data", "Top 10 News", "Technical Analysis"])

# Pricing data tab
with pricing_data:
    st.header('Price Movement')
    data2 = data.copy()
    data2['% Change'] = data['Adj Close'].pct_change()
    data2.dropna(inplace=True)
    st.write(data2)
    annual_return = data2['% Change'].mean() * 252 * 100
    st.write(f'Annual Return is {annual_return:.2f}%')
    stdev = np.std(data2['% Change']) * np.sqrt(252)
    st.write(f'Standard Deviation is {stdev:.2f}%')
    st.write(f'Risk Adjusted Return is {annual_return / stdev:.2f}')

# Fundamental data tab
from alpha_vantage.fundamentaldata import FundamentalData

with fundamental_data:
    key = 'YOUR_ALPHA_VANTAGE_API_KEY'
    fd = FundamentalData(key, output_format='pandas')
    st.subheader('Balance Sheet')
    balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
    bs = balance_sheet.T[2:]
    bs.columns = balance_sheet.T.iloc[0]
    st.write(bs)

    st.subheader('Income Statement')
    income_statement = fd.get_income_statement_annual(ticker)[0]
    is1 = income_statement.T[2:]
    is1.columns = income_statement.T.iloc[0]
    st.write(is1)

    st.subheader('Cash Flow Statement')
    cash_flow = fd.get_cash_flow_annual(ticker)[0]
    cf = cash_flow.T[2:]
    cf.columns = cash_flow.T.iloc[0]
    st.write(cf)

# News tab
from stocknews import StockNews

with news:
    st.header(f'News for {ticker}')
    sn = StockNews(ticker, save_news=False)
    df_news = sn.read_rss()
    for i in range(10):
        st.subheader(f'News {i + 1}')
        st.write(df_news['published'][i])
        st.write(df_news['title'][i])
        st.write(f'Title Sentiment: {df_news["sentiment_title"][i]}')
        st.write(f'News Sentiment: {df_news["sentiment_summary"][i]}')

# Chatbot section
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

st.title("💬 Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("api key")
        st.stop()

    openai.api_key = openai_api_key
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages
    )

    msg = response.choices[0].message["content"]
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
