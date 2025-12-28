import great_expectations as gx

context = gx.get_context()

raw_data = "~/github-projects/Active/experimental/data/raw"
clean_data = "~/github-projects/Active/experimental/data/processed"

# Define the data source
"""
sft_datasets = context.sources.pandas_default.read_csv(
    file_path=os.path.join(raw_data, "sft_datasets.csv")
)
"""

data_source = contxt.data_sources.add_pandas_filesystem(
    name = "my_local_datasource",
    base_directory = raw_data
)
