.PHONY: generate clean

PROTO_DIR = protos
GENERATED_DIR = generated

generate:
	python3 -m grpc_tools.protoc \
		-I$(PROTO_DIR) \
		--python_out=$(GENERATED_DIR) \
		--grpc_python_out=$(GENERATED_DIR) \
		$(PROTO_DIR)/*.proto
	# Create __init__.py if it doesn't exist
	touch $(GENERATED_DIR)/__init__.py

clean:
	rm -rf $(GENERATED_DIR)/* 