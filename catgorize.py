import os
import openai
from pathlib import Path
from openai.embeddings_utils import get_embedding, cosine_similarity

openai.api_key = os.getenv("OPENAI_API_KEY")
FOLDER_PATH = "topics"
EMBEDDING_MODEL = "text-embedding-ada-002"

def read_files(folder_path):
    files = {}
    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            with open(os.path.join(folder_path, file), "r") as f:
                files[file] = f.read()
    return files

def get_best_match(topic, files):
    topic_embedding = get_embedding(topic, engine=EMBEDDING_MODEL)
    scores = []
    for filename, content in files.items():
        file_embedding = get_embedding(content, engine=EMBEDDING_MODEL)
        similarity = cosine_similarity(topic_embedding, file_embedding)
        scores.append((filename, similarity))
    best_file = max(scores, key=lambda x: x[1])
    return best_file

def append_to_file(filename, topic):
    with open(os.path.join(FOLDER_PATH, filename), "a") as f:
        f.write(f"\n{topic}\n")

def main():
    topic = input("Enter a new topic: ")
    files = read_files(FOLDER_PATH)
    best_file, score = get_best_match(topic, files)
    append_to_file(best_file, topic)
    print(f"✅ Topic added to: {best_file} (Similarity Score: {score:.4f})")

if __name__ == "__main__":
    main()
