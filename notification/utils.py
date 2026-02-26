from firebase_admin import messaging

def send_fcm_notification(token, title, body, data=None):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=token,
    )

    response = messaging.send(message)
    print("FCM RESPONSE:", response)
    return response