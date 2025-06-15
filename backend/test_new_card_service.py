#!/usr/bin/env python3
"""
Script de test pour le service new_card_service.py
"""

import asyncio
import json
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Ajouter le chemin du projet pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.agent.new_card_service import create_new_card_from_prompt
    from app.services.github.schema import AgentRequest, TaskType
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous d'être dans le bon répertoire et que les modules existent.")
    sys.exit(1)


def create_mock_anthropic_response(response_data: dict) -> MagicMock:
    """Crée un mock de la réponse Anthropic."""
    message_mock = MagicMock()
    message_mock.content = [MagicMock()]
    message_mock.content[0].text = json.dumps(response_data)
    message_mock.model = "claude-sonnet-4-20250514"
    message_mock.usage = MagicMock()
    message_mock.usage.input_tokens = 150
    message_mock.usage.output_tokens = 200
    return message_mock


async def test_successful_card_creation():
    """Test de création réussie d'une nouvelle carte."""
    print("🧪 Test: Création réussie d'une carte")
    
    # Données de test
    request = AgentRequest(
        prompt="Research artificial intelligence applications in healthcare",
        context={"source": "test"}
    )
    
    mock_response = {
        "title": "AI Healthcare Research",
        "description": "Comprehensive research on AI applications in healthcare sector",
        "task_type": "research_task",
        "status": "todo",
        "parameters": {
            "topics": ["artificial intelligence", "healthcare", "medical technology"],
            "scope": "Current and future AI applications in healthcare industry"
        }
    }
    
    try:
        with patch('app.services.agent.new_card_service.claude_client') as mock_client:
            # Configuration du mock
            mock_client.messages.create = AsyncMock(
                return_value=create_mock_anthropic_response(mock_response)
            )
            
            # Exécution
            result = await create_new_card_from_prompt(request)
            
            # Vérifications
            assert result.card_data.title == "AI Healthcare Research"
            assert result.card_data.task_type == TaskType.RESEARCH
            assert result.card_data.status == "todo"
            assert len(result.card_data.parameters.topics) == 3
            assert "healthcare" in result.card_data.parameters.topics
            assert result.agent_id.startswith("new-card-func-")
            assert result.execution_time > 0
            assert result.metadata["model_used"] == "claude-sonnet-4-20250514"
            
            print("✅ Test réussi !")
            print(f"📋 Titre: {result.card_data.title}")
            print(f"🎯 Type: {result.card_data.task_type}")
            print(f"📊 Sujets: {', '.join(result.card_data.parameters.topics)}")
            print(f"⏱️ Temps d'exécution: {result.execution_time:.3f}s")
            print(f"🤖 Agent ID: {result.agent_id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


async def test_error_handling():
    """Test de gestion des erreurs."""
    print("\n🧪 Test: Gestion des erreurs")
    
    request = AgentRequest(
        prompt="Create a non-research task",
        context={"source": "test"}
    )
    
    error_response = {"error": "I can only handle research tasks."}
    
    try:
        with patch('app.services.agent.new_card_service.claude_client') as mock_client:
            # Configuration du mock pour retourner une erreur
            mock_client.messages.create = AsyncMock(
                return_value=create_mock_anthropic_response(error_response)
            )
            
            # Exécution - devrait lever une exception
            try:
                await create_new_card_from_prompt(request)
                print("❌ Erreur: L'exception attendue n'a pas été levée")
                return False
            except ValueError as e:
                if "I can only handle research tasks." in str(e):
                    print("✅ Gestion d'erreur correcte !")
                    print(f"📝 Message d'erreur: {e}")
                    return True
                else:
                    print(f"❌ Message d'erreur inattendu: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


async def test_invalid_json_response():
    """Test avec une réponse JSON invalide."""
    print("\n🧪 Test: Réponse JSON invalide")
    
    request = AgentRequest(
        prompt="Research blockchain technology",
        context={"source": "test"}
    )
    
    try:
        with patch('app.services.agent.new_card_service.claude_client') as mock_client:
            # Configuration du mock pour retourner du JSON invalide
            message_mock = MagicMock()
            message_mock.content = [MagicMock()]
            message_mock.content[0].text = "Invalid JSON response {{"
            mock_client.messages.create = AsyncMock(return_value=message_mock)
            
            # Exécution - devrait lever une exception
            try:
                await create_new_card_from_prompt(request)
                print("❌ Erreur: L'exception attendue n'a pas été levée")
                return False
            except ValueError as e:
                if "AI model returned invalid data" in str(e):
                    print("✅ Gestion d'erreur JSON correcte !")
                    print(f"📝 Message d'erreur: {e}")
                    return True
                else:
                    print(f"❌ Message d'erreur inattendu: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


async def test_anthropic_api_error():
    """Test avec une erreur de l'API Anthropic."""
    print("\n🧪 Test: Erreur API Anthropic")
    
    request = AgentRequest(
        prompt="Research machine learning algorithms",
        context={"source": "test"}
    )
    
    try:
        with patch('app.services.agent.new_card_service.claude_client') as mock_client:
            # Configuration du mock pour lever une erreur générique
            mock_client.messages.create = AsyncMock(
                side_effect=Exception("API service error")
            )
            
            # Exécution - devrait lever une exception
            try:
                await create_new_card_from_prompt(request)
                print("❌ Erreur: L'exception attendue n'a pas été levée")
                return False
            except Exception as e:
                # Pour ce test, on accepte n'importe quelle exception comme preuve que les erreurs sont gérées
                print("✅ Gestion d'erreur API correcte !")
                print(f"📝 Type d'erreur: {type(e).__name__}")
                print(f"📝 Message d'erreur: {e}")
                return True
                    
    except Exception as e:
        print(f"❌ Erreur inattendue dans le test: {e}")
        return False


async def main():
    """Fonction principale pour exécuter tous les tests."""
    print("🔥 Tests du service new_card_service.py")
    print("=" * 50)
    
    tests = [
        test_successful_card_creation,
        test_error_handling,
        test_invalid_json_response,
        test_anthropic_api_error,
    ]
    
    results = []
    for test_func in tests:
        result = await test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 Résultats des tests:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"  {i}. {test_func.__name__}: {status}")
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🏆 Tous les tests sont passés avec succès !")
    else:
        print("⚠️ Certains tests ont échoué.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrompus par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        sys.exit(1) 