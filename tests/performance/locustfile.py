from locust import HttpUser, task, between

class WebhookUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(10)
    def send_update(self):
        payload = {
            "update_id": 123456789,
            "message": {"message_id": 1, "from": {"id": 111, "is_bot": False, "first_name": "Test"}, "chat": {"id": 111}, "text": "Hello"}
        }
        self.client.post('/telegram/webhook', json=payload)

*** End Patch