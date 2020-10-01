import logging
from firebase_admin import messaging


def push(data=None, token=None):
    try:
        message = messaging.Message(
            data=data, token=token,
            apns=messaging.APNSConfig(),
            android=messaging.AndroidConfig(priority="high"),
            notification=messaging.Notification())
        messaging.send(message)
    except Exception as e:
        logging.exception(e)
