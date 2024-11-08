from flask import Flask, request, render_template
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

class SmaCross(bt.Strategy):
    params = (('sma1', 10), ('sma2', 30),)

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.params.sma1)
        sma2 = bt.ind.SMA(period=self.params.sma2)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/backtest', methods=['POST'])
def backtest():
    symbol = request.form['symbol']
    sma1 = int(request.form['sma1'])
    sma2 = int(request.form['sma2'])

    data = yf.download(symbol, start='2020-01-01', end='2023-01-01')
    data.dropna(inplace=True)
    data.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']

    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaCross, sma1=sma1, sma2=sma2)
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(10000.0)
    initial_cash = cerebro.broker.getvalue()
    cerebro.run()
    final_cash = cerebro.broker.getvalue()
    total_return = (final_cash - initial_cash) / initial_cash * 100

    # Plot the equity curve
    plt.figure(figsize=(10, 6))
    plt.plot(cerebro.broker.get_value_tracker())
    plt.title('Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    plt.grid(True)

    # Save the plot to a string buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()

    # Calculate Sharpe ratio and maximum drawdown
    # Note: These calculations are simplified for demonstration purposes
    sharpe_ratio = total_return / 100  # Simplified example
    max_drawdown = 0  # Placeholder for actual calculation

    results = {
        'symbol': symbol,
        'sma1': sma1,
        'sma2': sma2,
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown
        'plot_data': plot_data
    }

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')