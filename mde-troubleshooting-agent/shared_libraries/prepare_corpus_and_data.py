# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.auth import default
import vertexai
from vertexai.preview import rag
import os
from dotenv import load_dotenv, set_key

# Load environment variables from .env file
load_dotenv()

# --- Please fill in your configurations ---
# Retrieve the PROJECT_ID from the environmental variables.
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable not set. Please set it in your .env file."
    )
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
if not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_LOCATION environment variable not set. Please set it in your .env file."
    )
GCS_SOURCE_URI = os.getenv("GCS_SOURCE_URI")
if not GCS_SOURCE_URI:
    raise ValueError(
        "GCS_SOURCE_URI environment variable not set. Please set it in your .env file (e.g., gs://your-bucket/your-folder/*.pdf)."
    )
CORPUS_DISPLAY_NAME = "MDE_corpus"
CORPUS_DESCRIPTION = "Corpus containing documents from GCS"
ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


# --- Start of the script ---
def initialize_vertex_ai():
  credentials, _ = default()
  vertexai.init(
      project=PROJECT_ID, location=LOCATION, credentials=credentials
  )


def create_or_get_corpus():
  """Creates a new corpus or retrieves an existing one."""
  embedding_model_config = rag.EmbeddingModelConfig(
      publisher_model="publishers/google/models/text-embedding-004"
  )
  existing_corpora = rag.list_corpora()
  corpus = None
  for existing_corpus in existing_corpora:
    if existing_corpus.display_name == CORPUS_DISPLAY_NAME:
      corpus = existing_corpus
      print(f"Found existing corpus with display name '{CORPUS_DISPLAY_NAME}'")
      break
  if corpus is None:
    corpus = rag.create_corpus(
        display_name=CORPUS_DISPLAY_NAME,
        description=CORPUS_DESCRIPTION,
        embedding_model_config=embedding_model_config,
    )
    print(f"Created new corpus with display name '{CORPUS_DISPLAY_NAME}'")
  return corpus


def update_env_file(corpus_name, env_file_path):
    """Updates the .env file with the corpus name."""
    try:
        set_key(env_file_path, "RAG_CORPUS", corpus_name)
        print(f"Updated RAG_CORPUS in {env_file_path} to {corpus_name}")
    except Exception as e:
        print(f"Error updating .env file: {e}")

def list_corpus_files(corpus_name):
  """Lists files in the specified corpus."""
  files = list(rag.list_files(corpus_name=corpus_name))
  print(f"Total files in corpus: {len(files)}")
  for file in files:
    print(f"File: {file.display_name} - {file.name}")


def main():
  initialize_vertex_ai()
  corpus = create_or_get_corpus()

  # Update the .env file with the corpus name
  update_env_file(corpus.name, ENV_FILE_PATH)

  # Import files from GCS
  print(f"Importing files from GCS URI(s): {GCS_SOURCE_URI} into corpus {corpus.name}")
  try:
    # GCS_SOURCE_URI can be a single GCS URI or a glob pattern.
    # rag.import_files expects a list of URIs.
    import_response = rag.import_files(
        corpus.name,
        [GCS_SOURCE_URI],
        chunk_overlap=100,  # Optional: configure chunking
        chunk_size=500,     # Optional: configure chunking
    )
    print(f"Successfully initiated import of files. Imported: {import_response.imported_rag_files_count}, Failed: {import_response.failed_rag_files_count}")
  except Exception as e:
    print(f"Error importing files from GCS: {e}")

  # List all files in the corpus
  list_corpus_files(corpus_name=corpus.name)

if __name__ == "__main__":
  main()
