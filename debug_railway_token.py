#!/usr/bin/env python3
"""Debug Railway API token permissions and capabilities"""
import requests
import json
import base64

TOKEN = '4e97bf28-511b-4e29-b4d7-499bf7ce3221'
ENDPOINT = "https://backboard.railway.com/graphql/v2"

def decode_token_if_jwt():
    """Try to decode token if it's a JWT to see claims"""
    try:
        # Check if it's a JWT (has 3 parts separated by dots)
        parts = TOKEN.split('.')
        if len(parts) == 3:
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            print("Token payload:", json.loads(decoded))
    except:
        print("Token is not a JWT or couldn't be decoded")

def test_token_info():
    """Get information about the current token"""
    query = """
    query {
        me {
            id
            email
            name
            teams {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(ENDPOINT, json={"query": query}, headers=headers)
    print("Token info response:", json.dumps(response.json(), indent=2))

def test_service_domain_create():
    """Test creating a service domain (Railway subdomain) instead of custom domain"""
    mutation = """
    mutation CreateServiceDomain($input: ServiceDomainCreateInput!) {
        serviceDomainCreate(input: $input) {
            id
            domain
        }
    }
    """
    
    variables = {
        "input": {
            "environmentId": "e21cc1d5-20be-488c-b048-99ac534686dc",
            "serviceId": "18b0ec40-26f8-47fa-b254-606cdefe8feb"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting service domain creation...")
    response = requests.post(
        ENDPOINT, 
        json={"query": mutation, "variables": variables}, 
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def introspect_service_domain_input():
    """Get ServiceDomainCreateInput structure"""
    query = """
    query {
        __type(name: "ServiceDomainCreateInput") {
            name
            kind
            inputFields {
                name
                type {
                    name
                    kind
                    ofType {
                        name
                        kind
                    }
                }
            }
        }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(ENDPOINT, json={"query": query}, headers=headers)
    print("\nServiceDomainCreateInput structure:", json.dumps(response.json(), indent=2))

def test_different_token():
    """Test if a different token format works"""
    # Try without Bearer prefix
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    
    query = '{"query": "{ me { id } }"}'
    
    print("\nTesting without Bearer prefix...")
    response = requests.post(ENDPOINT, data=query, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    decode_token_if_jwt()
    test_token_info()
    introspect_service_domain_input()
    test_service_domain_create()
    test_different_token()