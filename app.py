from flask import Flask, request, jsonify
from bot import Bot
import json

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        bot = Bot(request.json)
        return bot.processing()
    return "Processing..."


if(__name__) == '__main__':
    app.run()
