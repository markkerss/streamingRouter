.PHONY: generate clean

PROTO_DIR = protos
GENERATED_DIR = generated

generate:
	# Create the generated directory if it doesn't exist
	mkdir -p $(GENERATED_DIR)
	
	# Generate proto files
	python3 -m grpc_tools.protoc \
		-I$(PROTO_DIR) \
		--python_out=$(GENERATED_DIR) \
		--grpc_python_out=$(GENERATED_DIR) \
		$(PROTO_DIR)/*.proto
	
	# Create __init__.py if it doesn't exist
	touch $(GENERATED_DIR)/__init__.py
	
	# Fix imports in generated files
	find $(GENERATED_DIR) -name "*_pb2.py" -type f -exec sed -i'' -e 's/^import \([a-z_]*\)_pb2/import generated.\1_pb2/g' {} +
	find $(GENERATED_DIR) -name "*_pb2_grpc.py" -type f -exec sed -i'' -e 's/^import \([a-z_]*\)_pb2 /import generated.\1_pb2 /g' {} +

clean:
	rm -rf $(GENERATED_DIR)/* 

run-server:
	PYTHONPATH=$(PYTHONPATH):$(PWD) python3 src/server.py

run-middleware:
	PYTHONPATH=$(PYTHONPATH):$(PWD) python3 src/middleware.py

run-client:
	PYTHONPATH=$(PYTHONPATH):$(PWD) python3 src/client.py