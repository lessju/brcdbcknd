from flask import Flask
app = Flask(__name__)

# Load barcode database
with open("database/barcodes.txt") as f:
    barcodes = [int(x) for x in f.readlines()]


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/authenticate_user')
def authenticate_user():
    return True


@app.route('/check_bar_code')
def check_bar_code():
    return True


if __name__ == "__main__":
    app.run("0.0.0.0", 8000, debug=True)


