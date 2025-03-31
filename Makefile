.PHONY: setup test clean format lint refresh-data query-llama setup-env debug-query create-dataset

# Default Python interpreter
PYTHON = python3
UV = uv

# AWS S3 bucket for data
S3_BUCKET = s3://ncsh-app-data
S3_PATH = v2/processed/parquet
DATAFILE = data.parquet
DATA_DIR = data

# Refresh data from AWS S3
refresh-data:
	@echo "Checking AWS S3 bucket $(S3_BUCKET)/$(S3_PATH) for data files..."
	aws s3 ls $(S3_BUCKET)/$(S3_PATH)
	@echo "Downloading $(DATAFILE) from S3 to $(DATA_DIR)/..."
	@mkdir -p $(DATA_DIR)

	# First create a backup of the current data if it exists
	@if [ -f "$(DATA_DIR)/data.parquet" ]; then \
		cp $(DATA_DIR)/data.parquet $(DATA_DIR)/data.backup.parquet; \
		echo "Created backup of existing data file"; \
	fi

	# Download main data file
	aws s3 cp $(S3_BUCKET)/$(S3_PATH)/$(DATAFILE) $(DATA_DIR)/data.parquet
	@echo "Successfully downloaded data to $(DATA_DIR)/data.parquet"

	# Check for additional datasets in the versioned directories
	@echo "Checking for additional datasets in versioned directories..."
	aws s3 ls $(S3_BUCKET)/$(S3_PATH)/ | grep "^PRE" | awk '{print $2}' | while read version; do \
		echo "Found version directory: $$version"; \
		mkdir -p $(DATA_DIR)/$$version; \
		aws s3 sync $(S3_BUCKET)/$(S3_PATH)/$$version $(DATA_DIR)/$$version; \
		echo "Synced files from $$version"; \
	done
	# List all downloaded datasets
	@echo "All available datasets:"
	@find $(DATA_DIR) -name "*.parquet" | sort
