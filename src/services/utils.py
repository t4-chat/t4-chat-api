import base64


def get_attachment_type(content_type: str) -> str:
    if content_type.startswith("image/"):
        return "image"
    elif content_type.startswith("audio/"):
        return "audio"
    elif content_type == "application/pdf":
        return "pdf"
    else:
        # This we just process as text for now
        return "text"


def prepare_file(content_type: str, file_data: bytes) -> str:
    encoded_file = base64.b64encode(file_data).decode("utf-8")
    base64_url = f"data:{content_type};base64,{encoded_file}"
    attachment_type = get_attachment_type(content_type)
    
    if attachment_type == "image":
        return {
            "type": "image_url",
            "image_url": {
                "url": base64_url
            }
        }
    elif attachment_type == "audio": # TODO: this is beta
        return {
            "type": "input_audio",
            "input_audio": {
                "url": {"data": base64_url, "format": "wav"}
            }
        }
    elif attachment_type == "pdf":
        return {
            "type": "file",
            "file": {
                "file_id": base64_url
            }
        }
    else:
        return {
            "type": "text",
            "text": file_data.decode('utf-8')
        }
