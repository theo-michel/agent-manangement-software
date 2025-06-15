#!/usr/bin/env python3
"""
Script de test pour l'API d'appels sortants Vapi
"""

import requests
import json


def test_outbound_call_api():
    """
    Test de la nouvelle route /chat/outbound-call
    """
    
    # URL de l'API (ajuste selon ton serveur)
    BASE_URL = "http://localhost:8000"  # Ou l'URL de ton serveur FastAPI
    endpoint = f"{BASE_URL}/chat/outbound-call"
    
    # Données de test
    test_data = {
        "target_number": "+33611421334",  # Ton numéro
        "market_overview": "The European ed-tech market grew 23% last year, with France and Germany leading demand in AI-powered language tools, while competition in the UK intensifies. New startups are emerging with innovative solutions for personalized learning.",
        "name": "Grégoire",
        "action_to_take": "Schedule a follow-up meeting to discuss potential partnership opportunities in the French market"
    }
    
    print("🔥 Test de l'API d'appels sortants Vapi")
    print(f"📞 Numéro cible: {test_data['target_number']}")
    print(f"👤 Nom: {test_data['name']}")
    print(f"🎯 Action: {test_data['action_to_take']}")
    print(f"📊 Market Overview: {test_data['market_overview'][:100]}...")
    print()
    
    try:
        # Envoi de la requête POST
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
            print(f"⚡ Temps d'exécution: {result.get('execution_time'):.2f}s")
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


if __name__ == "__main__":
    print("🧪 Tests de l'API\n")
    
    # Test de l'endpoint agent d'abord
    # test_simple_agent()
    # print("\n" + "="*50 + "\n")
    
    # Test de l'endpoint outbound call
    test_outbound_call_api()
    
    print("\n✨ Tests terminés !") 