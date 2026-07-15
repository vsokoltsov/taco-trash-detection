runtime: python312
service: default
entrypoint: streamlit run trash_annotation/ui.py --server.port $PORT --server.address 0.0.0.0 --server.headless true

instance_class: F2

env_variables:
  API_URL: "${API_URL}"
