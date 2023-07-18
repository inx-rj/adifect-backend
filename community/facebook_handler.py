import facebook

class FacebookAPIClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.api = facebook.GraphAPI(access_token=access_token, version='3.1')

    def post_story(self, message):
        try:
            self.api.put_object("me", "feed", message=message)
            return True
        except facebook.GraphAPIError as e:
            print(e, "Error")
            # Handle error scenarios
            return False
