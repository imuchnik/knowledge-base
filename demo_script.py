import requests
import time
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"

def create_sample_documents():
    docs = [
        ("sample_ml.txt", """Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. 
There are three main types of machine learning:

1. Supervised Learning: The algorithm learns from labeled training data. Examples include:
   - Classification: Predicting categories (spam detection, image classification)
   - Regression: Predicting continuous values (house prices, temperature)

2. Unsupervised Learning: The algorithm finds patterns in unlabeled data. Examples include:
   - Clustering: Grouping similar items (customer segmentation)
   - Dimensionality reduction: Simplifying complex data (PCA, t-SNE)

3. Reinforcement Learning: The algorithm learns through interaction with an environment.
   - Used in game playing, robotics, and autonomous systems
   - Learns from rewards and penalties

Common algorithms include decision trees, neural networks, support vector machines, and k-means clustering.
"""),
        ("sample_ai.txt", """Artificial Intelligence Overview

Artificial Intelligence (AI) is the simulation of human intelligence in machines. Key areas include:

- Natural Language Processing (NLP): Understanding and generating human language
- Computer Vision: Interpreting visual information from images and videos
- Expert Systems: Decision-making based on domain knowledge
- Neural Networks: Brain-inspired computational models

Deep learning, a subset of machine learning, uses multi-layered neural networks to learn complex patterns.
Applications include autonomous vehicles, medical diagnosis, and recommendation systems.

The field continues to evolve with advances in computing power and data availability.
"""),
        ("sample_data.txt", """Data Science Best Practices

Data science combines statistics, programming, and domain expertise. Key practices include:

1. Data Collection and Cleaning
   - Ensure data quality and consistency
   - Handle missing values appropriately
   - Remove duplicates and outliers

2. Exploratory Data Analysis (EDA)
   - Visualize data distributions
   - Identify patterns and correlations
   - Generate hypotheses

3. Feature Engineering
   - Create meaningful features from raw data
   - Scale and normalize features
   - Handle categorical variables

4. Model Selection and Evaluation
   - Choose appropriate algorithms
   - Use cross-validation
   - Monitor for overfitting

5. Communication
   - Present findings clearly
   - Use visualizations effectively
   - Tell a story with data
""")
    ]
    
    for filename, content in docs:
        with open(filename, 'w') as f:
            f.write(content)
    
    return [filename for filename, _ in docs]

def demo_upload_documents(filenames):
    print("📤 Uploading documents...")
    
    for filename in filenames:
        with open(filename, 'rb') as f:
            response = requests.post(
                f"{API_BASE_URL}/documents/upload",
                files={"file": (filename, f, "text/plain")}
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Uploaded {filename}: {data['chunks_processed']} chunks processed")
        else:
            print(f"❌ Failed to upload {filename}")
    
    print()

def demo_search():
    print("🔍 Demonstrating semantic search...")
    
    queries = [
        "types of machine learning algorithms",
        "neural networks and deep learning",
        "data visualization techniques"
    ]
    
    for query in queries:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={"query": query, "max_results": 3}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"\nQuery: '{query}'")
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results[:2], 1):
                print(f"  {i}. {result['filename']} (score: {result['similarity_score']:.3f})")
                print(f"     {result['content'][:100]}...")
    
    print()

def demo_qa():
    print("💬 Demonstrating Q&A system...")
    
    questions = [
        "What are the three main types of machine learning?",
        "How is deep learning related to artificial intelligence?",
        "What are the key steps in data science?"
    ]
    
    for question in questions:
        response = requests.post(
            f"{API_BASE_URL}/qa/ask",
            json={"question": question, "max_results": 3}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nQ: {question}")
            print(f"A: {data['answer'][:200]}...")
            print(f"Confidence: {data['confidence']:.2f}")
            print(f"Sources: {len(data['sources'])} documents")
    
    print()

def demo_completeness():
    print("📊 Checking knowledge base completeness...")
    
    response = requests.post(
        f"{API_BASE_URL}/qa/completeness",
        json={
            "topics": [
                "supervised learning",
                "unsupervised learning",
                "reinforcement learning",
                "deep learning architectures",
                "quantum computing"
            ]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nOverall Completeness: {data['overall_completeness']:.1%}")
        print("\nTopic Coverage:")
        for result in data['results']:
            print(f"  - {result['topic']}: {result['coverage_score']:.1%}")
            if result['missing_aspects']:
                print(f"    Missing: {', '.join(result['missing_aspects'][:2])}")
        
        print("\nRecommendations:")
        for rec in data['recommendations'][:2]:
            print(f"  - {rec}")
    
    print()

def demo_index_status():
    print("📈 Index Status:")
    
    response = requests.get(f"{API_BASE_URL}/index/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Total documents: {data['total_documents']}")
        print(f"  Total chunks: {data['total_chunks']}")
        print(f"  Index size: {data['index_size_mb']:.2f} MB")

def cleanup(filenames):
    for filename in filenames:
        if Path(filename).exists():
            Path(filename).unlink()

def main():
    print("🚀 Knowledge Base Search & Enrichment Demo\n")
    
    # Create sample documents
    filenames = create_sample_documents()
    
    try:
        # Run demos
        demo_upload_documents(filenames)
        time.sleep(1)  # Give the system time to process
        
        demo_search()
        demo_qa()
        demo_completeness()
        demo_index_status()
        
    finally:
        # Cleanup
        cleanup(filenames)
    
    print("\n✨ Demo completed!")

if __name__ == "__main__":
    main()