import requests
from flask import Flask, request, render_template, flash, redirect

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

def get_input():
    input_currency = ("")

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
        return render_template('results.html', rate=rate, from_currency=from_currency, to_currency=to_currency, convert_val = convert_val)
    else:
        flash('Failed to retrieve exchange rate.')
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
