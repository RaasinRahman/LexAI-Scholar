import os
from dotenv import load_dotenv
from vector_service import VectorService

load_dotenv()

def test_vector_service():
    print("=" * 60)
    print("VECTOR SERVICE DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Get Pinecone API key
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "pcsk_6uGvNp_3XAvNGrsf3LKYPzKq42ovqnHatj3J4RJzdx6xhmawsj9jza7K1nskPxsEQrDkfo")
    
    print(f"\n✓ Pinecone API Key: {pinecone_api_key[:20]}...")
    
    try:
        # Initialize vector service
        print("\n📦 Initializing Vector Service...")
        vector_service = VectorService(pinecone_api_key=pinecone_api_key)
        print("✓ Vector Service initialized successfully")
        
        # Get index stats
        print("\n📊 Getting Index Statistics...")
        stats = vector_service.get_index_stats()
        print(f"✓ Total vectors in index: {stats.get('total_vectors', 0)}")
        print(f"✓ Index dimension: {stats.get('dimension', 0)}")
        print(f"✓ Index fullness: {stats.get('index_fullness', 0)}")
        
        # Test embedding generation
        print("\n🧪 Testing Embedding Generation...")
        test_text = "What courses did I take in computer science?"
        embedding = vector_service.generate_embedding(test_text)
        print(f"✓ Generated embedding with dimension: {len(embedding)}")
        
        # Test search (with a dummy user_id to see what's in the index)
        print("\n🔍 Testing Search Functionality...")
        print("   Searching for: 'education university course'")
        
        # First, try without user filter to see if ANY vectors exist
        try:
            results = vector_service.index.query(
                vector=embedding,
                top_k=5,
                include_metadata=True
            )
            print(f"✓ Found {len(results.matches)} total vectors in index (no user filter)")
            
            if results.matches:
                print("\n📋 Sample results:")
                for i, match in enumerate(results.matches[:3], 1):
                    print(f"\n   Result {i}:")
                    print(f"   - Score: {match.score:.4f}")
                    print(f"   - User ID: {match.metadata.get('user_id', 'N/A')}")
                    print(f"   - Filename: {match.metadata.get('filename', 'N/A')}")
                    print(f"   - Text preview: {match.metadata.get('text', '')[:100]}...")
            else:
                print("\n⚠️  WARNING: No vectors found in index!")
                
        except Exception as e:
            print(f"✗ Search test failed: {e}")
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC TEST COMPLETE")
        print("=" * 60)
        
        print("\n💡 RECOMMENDATIONS:")
        if stats.get('total_vectors', 0) == 0:
            print("   1. No vectors in database - upload documents through the UI")
            print("   2. Check that PDF upload completes successfully")
            print("   3. Check backend logs for upload errors")
        else:
            print("   1. Vectors exist in database")
            print("   2. If search still fails, check user_id matching")
            print("   3. Try lowering min_score threshold (currently 0.3)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vector_service()

