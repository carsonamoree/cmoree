from flask import Flask, request
from threading import Thread
from pybit.unified_trading import HTTP
from time import sleep
import requests

app = Flask(__name__)

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1101655744677425293/J2e5vY2wVA6kCO9o2SSjrZ7Wi3s0PPs7mM1sUW1tNOvLK6P4yikFaU7oEYjuaRdEz8zF"


def send_discord_message(content):
    requests.post(DISCORD_WEBHOOK_URL, json={"content": content})


def pnl_report(session):
    pnl = session.get_pnl(category="linear", symbol="ETHUSDT")
    daily_pnl = pnl["result"]["dailyPnl"]
    closed_pnl = pnl["result"]["closedPnl"]
    all_time_pnl = daily_pnl + closed_pnl

    message = f"Daily PnL: {daily_pnl}\nAll Time PnL: {all_time_pnl}\nClosed PnL: {closed_pnl}"
    send_discord_message(message)


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    try:
        execute_trading_strategy(data)
    except Exception as e:
        send_discord_message(f"Error executing trading strategy: {e}")
        raise e

    return {'success': True}


def execute_trading_strategy(data):
    session = HTTP(
        testnet=False,
        api_key="YOUR_API_KEY",
        api_secret="YOUR_API_SECRET",
    )

    current_price = float(session.get_tickers(
        category="inverse",
        symbol="ETHUSDT",
    )["result"]["list"][0]["markPrice"])

    wallet_balance = session.get_wallet_balance(
        accountType="UNIFIED",
        coin="USDT",
    )

    total_balance = float(wallet_balance["result"]["list"][0]["totalAvailableBalance"])

    order_qty = (total_balance / current_price) * 3
    order_qty = round(order_qty, 4)

    side = data["side"]

    take_profit_price = current_price * 1.005 if side == "Buy" else current_price * 0.995
    take_profit_price = round(take_profit_price, 2)

    open_positions = session.get_positions(category="linear", symbol="ETHUSDT")["result"]["list"]

    if not open_positions:
        order_result = session.place_order(
            category="linear",
            symbol="ETHUSDT",
            side=side,
            orderType="Market",
            qty=order_qty,
            takeProfit=take_profit_price,
            tpTriggerBy="MarkPrice",
        )

        send_discord_message(f"Order placed:\n{order_result}")

        pnl_report(session)


if __name__ == '__main__':
    send_discord_message("Bot started")

    flask_thread = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 80})
    flask_thread.start()

    try:
        while True:
            sleep(86400)  # Sleep for a day
            send_discord_message("Bot is still running")
    except:
        send_discord_message("Bot stopped")
        raise
