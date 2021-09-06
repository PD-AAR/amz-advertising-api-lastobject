
web: functions-framework --target=main --debug --signature-type=http --host=0.0.0.0 --port=$PORT
worker: bash ./scripts/run_tests.sh && functions-framework --target=main --debug --signature-type=http --host=0.0.0.0 --port=$PORT