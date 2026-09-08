import socket
import traceback
import os
from dotenv import load_dotenv
import google.cloud.logging
from google.cloud.logging_v2.resource import Resource

load_dotenv()

# Set up Cloud Logging client (uses GOOGLE_APPLICATION_CREDENTIALS from .env)
client = google.cloud.logging.Client()
logger = client.logger("buggy-app")


def connect_to_database():
    # Deliberately wrong host/port to simulate a bad DB connection string
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5999"))  # intentionally wrong port

    print(f"Connecting to database at {db_host}:{db_port} ...")
    sock = socket.create_connection((db_host, db_port), timeout=3)
    return sock

def load_api_config():
    api_key = os.environ["EXTERNAL_API_KEY"]  # deliberately not set anywhere
    return api_key

def main():
    try:
        #connect_to_database()
        load_api_config()
        print("Connected successfully!")
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()

        print("ERROR OCCURRED:")
        print(stack_trace)

        # Send the error to Cloud Logging
        logger.log_struct(
            {
                "message": error_message,
                "stack_trace": stack_trace,
                "file": __file__,
            },
            severity="ERROR",
        )
        print("Error logged to Cloud Logging.")


if __name__ == "__main__":
    main()