runtime: python312
service: default
entrypoint: streamlit run trash_annotation/ui.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --server.enableWebsocketCompression=false

instance_class: F2

env_variables:
  API_URL: "${API_URL}"
