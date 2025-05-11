   
   
   
   
   
   
   
   
# class GithubDataService:
#     def __init__(self, github_service: GitHubService = None):
#         self.github_service = github_service

#     async def get_repository_status(
#         self, owner: str, repo: str, session: AsyncSession
#     ) -> RepositoryStatusResponse:
#         """
#         Get the status of a repository.
#         """
#         # Check if repository exists in the database
#         result = await session.execute(
#             select(Repository).where(Repository.full_name == f"{owner}/{repo}")
#         )
#         repository = result.scalars().first()

#         if repository:
#             return RepositoryStatusResponse(
#                 status=repository.status,
#                 file_count=len(repository.files) if repository.files else None,
#                 indexed_at=repository.indexed_at.isoformat() if repository.indexed_at else None,
#             )

#         # Repository not in database, get file count for estimation
#         try:
#             file_count = await self.github_service.count_files(owner, repo)
#             return RepositoryStatusResponse(
#                 status=SchemaRepoStatus.NOT_INDEXED,
#                 file_count=file_count,
#                 message="Repository not indexed yet",
#             )
#         except ValueError as e:
#             logger.error(f"Error getting file count: {str(e)}")
#             raise ValueError(f"Repository not found or access denied: {owner}/{repo}")
    
#     async def create_or_update_repository(
#         self, 
#         owner: str, 
#         repo: str, 
#         repo_info: Dict[str, Any],
#         status: RepoStatus,
#         session: AsyncSession
#     ) -> Repository:
#         """
#         Create or update a repository in the database.
#         """
#         # Check if repository already exists
#         result = await session.execute(
#             select(Repository).where(Repository.full_name == f"{owner}/{repo}")
#         )
#         repository = result.scalars().first()
        
#         if repository:
#             repository.status = status
#             repository.github_id = repo_info["id"]
#             repository.description = repo_info["description"]
#             repository.default_branch = repo_info["default_branch"]
#             repository.stars = repo_info["stars"]
#             repository.forks = repo_info["forks"]
#             repository.size = repo_info["size"]
#             repository.updated_at = datetime.utcnow()
#         else:
#             repository = Repository(
#                 github_id=repo_info["id"],
#                 owner=owner,
#                 name=repo,
#                 full_name=f"{owner}/{repo}",
#                 description=repo_info["description"],
#                 default_branch=repo_info["default_branch"],
#                 stars=repo_info["stars"],
#                 forks=repo_info["forks"],
#                 size=repo_info["size"],
#                 status=status,
#             )
#             session.add(repository)
        
#         await session.commit()
#         await session.refresh(repository)
#         return repository