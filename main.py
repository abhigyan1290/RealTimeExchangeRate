import requests
from flask import Flask, request, render_template, flash, redirect, url_for
import time
import yfinance as yf
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_all_currencies():
    response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
    data = response.json()
    return list(data['rates'].keys())

def get_rate(from_currency, to_currency):
    response = requests.get(f'https://api.exchangerate-api.com/v4/latest/{from_currency}')
    if response.status_code == 200:
        rates = response.json()
        if to_currency in rates['rates']:
            return rates['rates'][to_currency]
        else:
            return None
    else:
        return None

def get_historical_data(from_currency, to_currency, period):
    # List of possible ticker formats
    possible_tickers = [
        f"{from_currency}{to_currency}=X",
        f"{to_currency}{from_currency}=X"
    ]
    for ticker in possible_tickers:
        print(f"Attempting to download data for ticker: {ticker}")
        try:
            data = yf.download(ticker, period=period, interval='1d')
            print(f"Data downloaded for ticker: {ticker}, data empty: {data.empty}")
            if not data.empty:
                # Compute momentum
                data['Momentum'] = data['Close'] - data['Close'].shift(10)
                data['Momentum_sign'] = data['Momentum'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
                data['Momentum_sign_change'] = data['Momentum_sign'].diff()
                # Find buy and sell signals
                buy_signals = data[data['Momentum_sign_change'] == 2]
                sell_signals = data[data['Momentum_sign_change'] == -2]
                # Generate plot
                fig, ax1 = plt.subplots(figsize=(10,6))
                ax1.plot(data.index, data['Close'], color='b', label='Close Price')
                ax1.set_xlabel('Date')
                ax1.set_ylabel('Exchange Rate', color='b')
                ax1.tick_params(axis='y', labelcolor='b')
                # Mark buy signals
                ax1.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='g', label='Buy Signal')
                # Mark sell signals
                ax1.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='r', label='Sell Signal')
                ax1.legend(loc='upper left')
                # Second y-axis for Momentum
                ax2 = ax1.twinx()
                ax2.plot(data.index, data['Momentum'], color='grey', alpha=0.3, label='Momentum')
                ax2.set_ylabel('Momentum', color='grey')
                ax2.tick_params(axis='y', labelcolor='grey')
                ax2.legend(loc='lower right')
                plt.title(f"{from_currency}/{to_currency} Exchange Rate and Momentum over {period}")
                plt.grid(True)
                # Save plot to a file
                image_filename = f'{from_currency}_{to_currency}_{period}.png'
                static_path = os.path.join('static', image_filename)
                plt.savefig(static_path)
                plt.close()
                return image_filename
        except Exception as e:
            print(f"Error downloading data for ticker {ticker}: {e}")
    # If no valid data was found
    return None

@app.route('/')
def upload_form():
    currencies = get_all_currencies()
    return render_template('upload.html', currencies=currencies)

@app.route('/convert', methods=['POST'])
def convert_currency():
    from_currency = request.form.get('from_currency')
    to_currency = request.form.get('to_currency')
    amount = request.form.get('amount')

    if amount:
        amount = float(amount)
    else:
        flash("Please enter valid amount.")
        return redirect('/')

    rate = get_rate(from_currency, to_currency)
    if rate:
        convert_val = amount * rate
        return render_template('results.html', rate=rate, from_currency=from_currency, to_currency=to_currency, convert_val=convert_val)
    else:
        flash('Failed to retrieve exchange rate.')
        return redirect('/')

@app.route('/history', methods=['GET', 'POST'])
def currency_history():
    if request.method == 'POST':
        from_currency = request.form.get('from_currency')
        to_currency = request.form.get('to_currency')
        period = request.form.get('period')  # E.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'

        image_filename = get_historical_data(from_currency, to_currency, period)

        if image_filename:
            return render_template('history.html', image_filename=image_filename, from_currency=from_currency, to_currency=to_currency, period=period)
        else:
            flash('Failed to retrieve historical data.')
            return redirect('/history')
    else:
        currencies = get_all_currencies()
        periods = {
            '1 Day': '1d',
            '5 Days': '5d',
            '1 Month': '1mo',
            '3 Months': '3mo',
            '6 Months': '6mo',
            '1 Year': '1y',
            '2 Years': '2y',
            '5 Years': '5y'
        }
        return render_template('history_form.html', currencies=currencies, periods=periods)

if __name__ == '__main__':
    app.run(debug=True)
