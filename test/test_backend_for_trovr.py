import requests
import time

backend_url = "http://127.0.0.1:8000"
keepalive_endpoint = "bin_keepalive"
confirm_user_endpoint = "confirm_user"
verify_barcode_endpoint = "verify_barcode"
confirm_barcode_endpoint = "confirm_barcode"
get_session_bottles_endpoint = "get_session_bottles"
reject_barcode_endpoint = "reject_barcode"
end_user_session_endpoint = "end_user_session"


def check_backend_online():
    """ Check that backend is online """
    requests.get(backend_url)


def send_request(endpoint, values=None):
    """ Send request to server, including the providing JSON values """

    # If values are provided send then as json body in request
    if values is not None:
        response = requests.post(f"{backend_url}/{endpoint}", json=values)
    else:
        response = requests.get(f"{backend_url}/{endpoint}")

    # Return json reply
    return response.json()


check_backend_online()
print(send_request(confirm_user_endpoint, {'user_id': 12345678}))
print(send_request(confirm_barcode_endpoint, {'user_id': 12345678, 'barcode': 54491496}))
print(send_request(confirm_barcode_endpoint, {'user_id': 12345678, 'barcode': 54491496}))
print(send_request(confirm_barcode_endpoint, {'user_id': 12345678, 'barcode': 54491496}))
print(send_request(reject_barcode_endpoint, {'user_id': 12345678, 'barcode': 54491496888}))
print(send_request(end_user_session_endpoint, {'user_id': 12345678}))
print(send_request(get_session_bottles_endpoint, {'user_id': 12345678}))
