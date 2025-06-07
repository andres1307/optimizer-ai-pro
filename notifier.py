from win10toast import ToastNotifier

class Notifier:
    def __init__(self):
        self.toaster = ToastNotifier()

    def send_notification(self, title, msg):
        self.toaster.show_toast(title, msg, duration=5, threaded=True)
