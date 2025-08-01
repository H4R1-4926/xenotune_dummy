import os, json
import firebase_admin
from firebase_admin import credentials, storage
 
firebase_initialized = False
firebase_key_path = "firebase_key.json"

def write_service_account_file():
    key_content = os.getenv("FIREBASE_CRED_PATH", "assets/serviceAccountKey.json")
    # key_content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not key_content:
        raise RuntimeError("Firebase key not found in environment variables.")

    # Save the JSON content to a file
    with open(firebase_key_path, "w") as f:
        json.dump(json.loads(key_content), f)

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_key_path

def init_firebase():
    global firebase_initialized
    if firebase_initialized:
        return

    write_service_account_file()

    if not os.path.exists(firebase_key_path):
        raise FileNotFoundError(f"Firebase credential file not found at: {firebase_key_path}")

    cred = credentials.Certificate(firebase_key_path)
      
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_BUCKET', 'xenotune-fromx.appspot.com')  # ✅ corrected bucket name
    })

    firebase_initialized = True

# def init_firebase():
#     global firebase_initialized
#     if not firebase_initialized:
#         cred_path = os.getenv("FIREBASE_CRED_PATH", "assets/serviceAccountKey.json")
#         if not os.path.exists(cred_path):
#             raise FileNotFoundError(f"Firebase credential file not found at: {cred_path}")

#         cred = credentials.Certificate(cred_path)
#         firebase_admin.initialize_app(cred, {
#             'storageBucket': os.getenv('FIREBASE_BUCKET', 'xenotune-fromx.firebasestorage.app')
#         })
#         firebase_initialized = True
 
 
def upload_to_firebase(local_file_path: str, firebase_path: str) -> str:

    # Ensure Firebase is initialized
    init_firebase()
 
    if not os.path.isfile(local_file_path):
        raise FileNotFoundError(f"❌ File not found: {local_file_path}")
 
    try:
        bucket = storage.bucket()
        blob = bucket.blob(firebase_path)
        blob.cache_control = "no-cache" 
        blob.upload_from_filename(local_file_path)
        blob.make_public()
        blob.patch()
 
        public_url = blob.public_url
        print(f"✅ Uploaded to Firebase Storage: {public_url}")
        return public_url
 
    except Exception as e:
        print(f"❌ Failed to upload to Firebase: {e}")
        raise
 
 
if __name__ == "__main__":
    # Example usage with default env settings
    try:
        url = upload_to_firebase('output/music.mp3', 'generated_music/music.mp3')
        print(f"Public URL: {url}")
    except Exception as e:
        print(f"Error: {e}")
 