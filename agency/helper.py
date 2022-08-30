import base64

class StringEncoder:
    "This is  encoder decoder class"

    def encode(self, value):
        byte_msg = str(value).encode('ascii')
        base64_value = base64.b64encode(byte_msg)
        idDecoded = base64_value.decode('ascii')
        idDecoded = idDecoded.strip()
        return idDecoded

    def decode(self, value):
        byte_msg = value.encode('ascii')
        base64_val = base64.b64decode(byte_msg)
        encoded_id = base64_val.decode('ascii')
        return encoded_id
