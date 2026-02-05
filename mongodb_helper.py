"""
MongoDB URI Helper Script
Use this to properly encode your MongoDB credentials if they contain special characters
"""
from urllib.parse import quote_plus
import re


def encode_credentials(username: str, password: str) -> tuple:
    """
    URL-encode username and password for MongoDB URI
    
    Args:
        username: MongoDB username
        password: MongoDB password
        
    Returns:
        Tuple of (encoded_username, encoded_password)
    """
    return quote_plus(username), quote_plus(password)


def build_mongodb_uri(username: str, password: str, cluster: str) -> str:
    """
    Build a properly formatted MongoDB Atlas URI
    
    Args:
        username: MongoDB username
        password: MongoDB password (will be auto-encoded)
        cluster: Cluster address (e.g., cluster0.abc123.mongodb.net)
        
    Returns:
        Complete MongoDB URI
    """
    encoded_user, encoded_pass = encode_credentials(username, password)
    return f"mongodb+srv://{encoded_user}:{encoded_pass}@{cluster}/?retryWrites=true&w=majority"


def validate_uri(uri: str) -> dict:
    """
    Validate and parse a MongoDB URI
    
    Args:
        uri: MongoDB connection string
        
    Returns:
        Dict with validation results
    """
    pattern = r'mongodb\+srv://([^:]+):([^@]+)@(.+)'
    match = re.match(pattern, uri)
    
    if not match:
        return {
            "valid": False,
            "error": "Invalid URI format. Expected: mongodb+srv://USERNAME:PASSWORD@CLUSTER/"
        }
    
    username, password, cluster = match.groups()
    
    # Check for common issues
    issues = []
    
    if '@' in username:
        issues.append("Username contains '@' - it will be auto-encoded")
    
    if username.lower() in password.lower():
        issues.append("⚠️  Password should not be the same as username")
    
    if password == "YOUR_PASSWORD":
        issues.append("❌ You need to replace 'YOUR_PASSWORD' with your actual password")
    
    return {
        "valid": True,
        "username": username,
        "cluster": cluster.split('/')[0] if '/' in cluster else cluster,
        "issues": issues if issues else ["✓ URI format looks good"]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB URI Helper")
    print("=" * 60)
    print()
    
    # Interactive mode
    print("This tool helps you create a properly formatted MongoDB URI")
    print()
    
    choice = input("Choose an option:\n1. Build new URI\n2. Validate existing URI\n\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 60)
        print("Build MongoDB URI")
        print("=" * 60)
        
        username = input("\nEnter MongoDB username: ").strip()
        password = input("Enter MongoDB password: ").strip()
        cluster = input("Enter cluster address (e.g., cluster0.abc123.mongodb.net): ").strip()
        
        # Build URI
        uri = build_mongodb_uri(username, password, cluster)
        
        print("\n" + "=" * 60)
        print("Your MongoDB URI:")
        print("=" * 60)
        print(uri)
        print("\n✓ Username and password have been properly URL-encoded")
        print("\nCopy this URI to your .env file:")
        print(f"MONGODB_URI={uri}")
        
    elif choice == "2":
        print("\n" + "=" * 60)
        print("Validate MongoDB URI")
        print("=" * 60)
        
        uri = input("\nPaste your MongoDB URI: ").strip()
        
        result = validate_uri(uri)
        
        print("\n" + "=" * 60)
        print("Validation Results:")
        print("=" * 60)
        
        if result["valid"]:
            print(f"✓ Valid URI format")
            print(f"\nUsername: {result['username']}")
            print(f"Cluster:  {result['cluster']}")
            print("\nIssues/Notes:")
            for issue in result["issues"]:
                print(f"  {issue}")
        else:
            print(f"✗ {result['error']}")
        
    else:
        print("Invalid choice. Run the script again.")
    
    print("\n" + "=" * 60)
    
    # Always show encoding examples
    print("\nCommon Special Characters That Need Encoding:")
    print("=" * 60)
    examples = [
        ("@", "%40"),
        (":", "%3A"),
        ("/", "%2F"),
        ("?", "%3F"),
        ("#", "%23"),
        ("[", "%5B"),
        ("]", "%5D"),
        ("!", "%21"),
        ("$", "%24"),
        ("&", "%26"),
        ("'", "%27"),
        ("(", "%28"),
        (")", "%29"),
        ("*", "%2A"),
        ("+", "%2B"),
        (",", "%2C"),
        (";", "%3B"),
        ("=", "%3D"),
        ("%", "%25"),
    ]
    
    for char, encoded in examples[:5]:  # Show first 5
        print(f"  '{char}' → '{encoded}'")
    print(f"\n  (and {len(examples) - 5} more...)")
    
    print("\nNote: The backend automatically handles encoding now!")
    print("Just make sure your URI format is correct in .env")
    print("=" * 60)
