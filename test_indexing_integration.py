import asyncio
import os
import sys
sys.path.append('backend')

from backend.app.services.indexer.service import IndexerService
from backend.app.db.github_data_service import GithubDataService
from backend.app.database import get_async_session
from backend.app.models.models import Repository, RepositoryFile, CodeUnit, RepoStatus
from sqlalchemy import select
import json

async def test_indexing_and_db_integration():
    print('=== Testing Indexing and Database Integration ===')
    
    # Initialize services
    indexer_service = IndexerService()
    github_data_service = GithubDataService()
    
    # Test repository
    owner = 'julien-blanchon'
    repo = 'arxflix'
    
    try:
        # Get database session
        async for session in get_async_session():
            print(f'Testing repository: {owner}/{repo}')
            
            # Test 1: Check initial status
            print('\n1. Checking initial repository status...')
            try:
                status = await github_data_service.get_repository_status(owner, repo, session)
                print(f'Initial status: {status.status}')
            except Exception as e:
                print(f'Repository not found in database (expected): {e}')
            
            # Test 2: Run indexing with database integration
            print('\n2. Running indexing with database integration...')
            cache_name = await indexer_service.save_indexed_data_to_db(
                owner=owner,
                repo=repo,
                session=session,
                gemini_api_key=os.getenv('GEMINI_API_KEY')
            )
            print(f'Indexing completed. Cache name: {cache_name}')
            
            # Test 3: Verify repository was created/updated
            print('\n3. Verifying repository in database...')
            result = await session.execute(
                select(Repository).where(Repository.full_name == f'{owner}/{repo}')
            )
            repository = result.scalars().first()
            
            if repository:
                print(f'✓ Repository found: {repository.full_name}')
                print(f'  Status: {repository.status}')
                print(f'  Indexed at: {repository.indexed_at}')
                print(f'  Description: {repository.description[:100] if repository.description else "None"}...')
            else:
                print('✗ Repository not found in database')
                return
            
            # Test 4: Verify repository files were saved
            print('\n4. Verifying repository files...')
            result = await session.execute(
                select(RepositoryFile).where(RepositoryFile.repository_id == repository.id)
            )
            files = result.scalars().all()
            
            print(f'✓ Found {len(files)} files in database')
            if files:
                for i, file in enumerate(files[:5]):  # Show first 5 files
                    print(f'  File {i+1}: {file.path} ({file.language}) - {file.description[:50] if file.description else "No description"}...')
                if len(files) > 5:
                    print(f'  ... and {len(files) - 5} more files')
            
            # Test 5: Verify code units were saved
            print('\n5. Verifying code units...')
            result = await session.execute(
                select(CodeUnit).where(CodeUnit.repository_id == repository.id)
            )
            code_units = result.scalars().all()
            
            print(f'✓ Found {len(code_units)} code units in database')
            if code_units:
                # Group by type
                functions = [cu for cu in code_units if cu.type == 'function']
                classes = [cu for cu in code_units if cu.type == 'class']
                methods = [cu for cu in code_units if cu.type == 'method']
                
                print(f'  Functions: {len(functions)}')
                print(f'  Classes: {len(classes)}')
                print(f'  Methods: {len(methods)}')
                
                # Show some examples
                if functions:
                    print(f'  Example function: {functions[0].name} - {functions[0].description[:50] if functions[0].description else "No description"}...')
                if classes:
                    print(f'  Example class: {classes[0].name} - {classes[0].description[:50] if classes[0].description else "No description"}...')
            
            # Test 6: Verify JSON files were created
            print('\n6. Verifying JSON files were created...')
            json_files = [
                f'docstrings_json/{repo}.json',
                f'ducomentations_json/{repo}.json',
                f'configs_json/{repo}.json'
            ]
            
            for json_file in json_files:
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    print(f'✓ {json_file} exists with {len(str(data))} characters')
                else:
                    print(f'✗ {json_file} not found')
            
            # Test 7: Test repository status endpoint
            print('\n7. Testing repository status after indexing...')
            final_status = await github_data_service.get_repository_status(owner, repo, session)
            print(f'Final status: {final_status.status}')
            print(f'File count: {final_status.file_count}')
            print(f'Indexed at: {final_status.indexed_at}')
            
            print('\n=== Test completed successfully! ===')
            break
            
    except Exception as e:
        print(f'\n✗ Test failed with error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_indexing_and_db_integration()) 