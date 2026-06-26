from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "status": "error",
            "message": response.data.get('detail', 'An error occurred'),
            "errors": response.data if not isinstance(response.data, dict) else response.data
        }
    return response