#!/usr/bin/env python3
"""
Script de test pour tous les endpoints de l'API interface.py
"""

import requests
import json
import time


def test_agent_endpoint():
    """
    Test de l'endpoint /chat/agent
    """
    
    BASE_URL = "http://localhost:8000"
    endpoint = f"{BASE_URL}/chat/agent"
    
    test_data = {
        "prompt": "Analyze the current state of AI in healthcare and provide insights on emerging trends"
    }
    
    print("🤖 Test de l'endpoint /chat/agent")
    print(f"💬 Prompt: {test_data['prompt']}")
    print()
    
    try:
        print("📤 Envoi de la requête...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📝 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📋 Response: {result.get('response', 'N/A')[:200]}...")
            if result.get('metadata'):
                print("📊 Métadonnées:")
                for key, value in result['metadata'].items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Erreur !")
            try:
                error_detail = response.json()
                print(f"📋 Détail: {error_detail}")
            except:
                print(f"📋 Réponse: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def test_outbound_call_endpoint():
    """
    Test de l'endpoint /chat/outbound-call
    """
    
    BASE_URL = "http://localhost:8000"
    endpoint = f"{BASE_URL}/chat/outbound-call"
    
    test_data = {
        "target_number": "+33611421334",
        "market_overview": "The European ed-tech market grew 23% last year, with France and Germany leading demand in AI-powered language tools, while competition in the UK intensifies. New startups are emerging with innovative solutions for personalized learning.",
        "name": "Grégoire",
        "action_to_take": "Schedule a follow-up meeting to discuss potential partnership opportunities in the French market"
    }
    
    print("📞 Test de l'endpoint /chat/outbound-call")
    print(f"📞 Numéro cible: {test_data['target_number']}")
    print(f"👤 Nom: {test_data['name']}")
    print(f"🎯 Action: {test_data['action_to_take']}")
    print(f"📊 Market Overview: {test_data['market_overview'][:100]}...")
    print()
    
    try:
        print("📤 Envoi de la requête...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📝 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📞 Call ID: {result.get('call_id')}")
            print(f"⚡ Temps d'exécution: {result.get('execution_time', 0):.2f}s")
            print(f"📋 Message: {result.get('message')}")
            
            if result.get('metadata'):
                print("📊 Métadonnées:")
                for key, value in result['metadata'].items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Erreur !")
            try:
                error_detail = response.json()
                print(f"📋 Détail: {error_detail}")
            except:
                print(f"📋 Réponse: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def test_new_card_endpoint():
    """
    Test de l'endpoint /chat/new-card
    """
    
    BASE_URL = "http://localhost:8000"
    endpoint = f"{BASE_URL}/chat/new-card"
    
    test_data = {
        "prompt": "Create a task to implement user authentication with OAuth2 for our web application, including login, logout, and session management features"
    }
    
    print("📋 Test de l'endpoint /chat/new-card")
    print(f"💬 Prompt: {test_data['prompt']}")
    print()
    
    try:
        print("📤 Envoi de la requête...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📝 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📋 Titre: {result.get('title', 'N/A')}")
            print(f"📝 Description: {result.get('description', 'N/A')[:200]}...")
            print(f"🏷️ Labels: {result.get('labels', [])}")
            print(f"⚡ Priorité: {result.get('priority', 'N/A')}")
            print(f"📅 Estimation: {result.get('estimation', 'N/A')}")
            
            if result.get('metadata'):
                print("📊 Métadonnées:")
                for key, value in result['metadata'].items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Erreur !")
            try:
                error_detail = response.json()
                print(f"📋 Détail: {error_detail}")
            except:
                print(f"📋 Réponse: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def test_deep_search_endpoint():
    """
    Test de l'endpoint /chat/deep-search
    """
    
    BASE_URL = "http://localhost:8000"
    endpoint = f"{BASE_URL}/chat/deep-search"
    
    test_data = {
        "prompt": "What are the latest developments in quantum computing and their potential impact on cybersecurity?"
    }
    
    print("🔍 Test de l'endpoint /chat/deep-search")
    print(f"💬 Prompt: {test_data['prompt']}")
    print()
    
    try:
        print("📤 Envoi de la requête...")
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # Plus long timeout pour la recherche web
        )
        
        print(f"📝 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Succès !")
            print(f"📋 Response: {result.get('response', 'N/A')[:300]}...")
            
            if result.get('sources'):
                print("🔗 Sources:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"   {i}. {source}")
            
            if result.get('metadata'):
                print("📊 Métadonnées:")
                for key, value in result['metadata'].items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Erreur !")
            try:
                error_detail = response.json()
                print(f"📋 Détail: {error_detail}")
            except:
                print(f"📋 Réponse: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")


def test_empty_prompt_validation():
    """
    Test de validation des prompts vides pour les endpoints qui le requièrent
    """
    
    BASE_URL = "http://localhost:8000"
    endpoints_to_test = [
        "/chat/new-card",
        "/chat/deep-search"
    ]
    
    print("🚫 Test de validation des prompts vides")
    
    for endpoint_path in endpoints_to_test:
        endpoint = f"{BASE_URL}{endpoint_path}"
        test_data = {"prompt": ""}  # Prompt vide
        
        print(f"   Testing {endpoint_path}...")
        
        try:
            response = requests.post(
                endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 400:
                print(f"   ✅ {endpoint_path}: Validation OK (400)")
            else:
                print(f"   ❌ {endpoint_path}: Expected 400, got {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint_path}: Erreur - {e}")


if __name__ == "__main__":
    print("🧪 Tests complets de l'API Interface\n")
    
    # Test de chaque endpoint
    test_agent_endpoint()
    print("\n" + "="*60 + "\n")
    
    test_outbound_call_endpoint()
    print("\n" + "="*60 + "\n")
    
    test_new_card_endpoint()
    print("\n" + "="*60 + "\n")
    
    test_deep_search_endpoint()
    print("\n" + "="*60 + "\n")
    
    # Test de validation
    test_empty_prompt_validation()
    
    print("\n✨ Tous les tests terminés !")
