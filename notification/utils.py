from firebase_admin import messaging


def send_fcm_notification(token, title, body, data=None):
    message = messaging.Message(
        data={
            "title": title,
            "body": body,
            **(data or {}),
        },
        token=token,
    )

    response = messaging.send(message)
    return response
