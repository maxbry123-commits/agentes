#!/usr/bin/env python
"""
Script to test moving a single Hugging Face repository.
Example usage: 
    python move_hf_test.py --from "mlfoundations-dev/fig1_all_openthoughts" --to "mlfoundations-dev/openthoughts"
    python move_hf_test.py --from "mlfoundations-dev/fig1_all_openthoughts" --replace-prefix "figure1_"
"""

import argparse
import os
from huggingface_hub import move_repo, login, list_models, list_datasets

def check_repo_exists(repo_id):
    """
    Check if a repository exists as a model or dataset.
    
    Args:
        repo_id (str): Repository ID to check
        
    Returns:
        tuple: (exists, type) where type is 'model', 'dataset', or None if it doesn't exist
    """
    # Check if it's a model
    models = list_models(author=repo_id.split('/')[0])
    for model in models:
        if model.modelId == repo_id:
            return True, 'model'
    
    # Check if it's a dataset
    datasets = list_datasets(author=repo_id.split('/')[0])
    for dataset in datasets:
        if dataset.id == repo_id:
            return True, 'dataset'
    
    return False, None

def move_single_repo(from_id, to_id=None, prefix=None, replace_prefix=None, repo_type=None, dry_run=False):
    """
    Move a single repository from from_id to to_id, or replace a prefix.
    
    Args:
        from_id (str): Source repository ID
        to_id (str): Destination repository ID. If None, will be computed from prefix/replace_prefix
        prefix (str): Prefix to replace. Required if to_id is None.
        replace_prefix (str): New prefix to use. If None, the prefix will be removed.
        repo_type (str): Type of repository ('model', 'dataset', or None for auto-detect)
        dry_run (bool): If True, only print what would be moved without actually moving
    """
    # Build destination ID if not provided
    if to_id is None:
        if prefix is None:
            raise ValueError("Either to_id or prefix must be provided")
        
        org, repo_name = from_id.split('/')
        if not repo_name.startswith(prefix):
            raise ValueError(f"Repository name {repo_name} does not start with prefix {prefix}")
        
        if replace_prefix is not None:
            new_name = replace_prefix + repo_name[len(prefix):]
        else:
            new_name = repo_name[len(prefix):]
        
        to_id = f"{org}/{new_name}"
    
    # Check if repo exists and auto-detect type if not specified
    if not repo_type:
        exists, detected_type = check_repo_exists(from_id)
        if exists:
            repo_type = detected_type
            print(f"Repository detected as: {repo_type}")
        else:
            print(f"Warning: Repository {from_id} not found as either model or dataset")
    
    print(f"Moving repository ({repo_type}): {from_id} -> {to_id}")
    
    if not dry_run:
        try:
            move_repo(from_id=from_id, to_id=to_id, repo_type=repo_type)
            print(f"✅ Successfully moved {from_id} to {to_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to move {from_id}: {str(e)}")
            # If it's a conflict error (409), provide a link to the conflicting resource
            if "409 Client Error: Conflict" in str(e):
                print(f"⚠️  Conflicting repository exists at: https://huggingface.co/{to_id}")
            return False
    else:
        print("Dry run mode - no changes made")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test moving a single Hugging Face repository")
    parser.add_argument("--from", dest="from_id", required=True, help="Source repository ID (e.g., 'mlfoundations-dev/repo_name')")
    parser.add_argument("--to", dest="to_id", help="Destination repository ID (e.g., 'mlfoundations-dev/new_name')")
    parser.add_argument("--prefix", help="Prefix to replace in the repository name (used if --to is not specified)")
    parser.add_argument("--replace-prefix", help="Replace the prefix with this new prefix instead of removing it")
    parser.add_argument("--type", choices=["model", "dataset"], help="Type of repository ('model' or 'dataset'). If not specified, auto-detect.")
    parser.add_argument("--token", help="Hugging Face API token (alternatively, set the HF_TOKEN environment variable)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be moved without moving anything")
    parser.add_argument("--list-only", action="store_true", help="Just list repositories without moving anything")
    
    args = parser.parse_args()
    
    # Authenticate with Hugging Face
    token = args.token or os.environ.get("HF_TOKEN")
    if token:
        print("Authenticating with Hugging Face...")
        login(token=token)
    else:
        print("Warning: No Hugging Face token provided. You may encounter authentication errors.")
        print("Set the HF_TOKEN environment variable or provide --token.")
    
    # Just list repositories if requested
    if args.list_only:
        org = args.from_id.split('/')[0]
        print(f"Listing models for {org}:")
        models = list_models(author=org)
        for model in models:
            print(f"Model: {model.modelId}")
        
        print(f"\nListing datasets for {org}:")
        datasets = list_datasets(author=org)
        for dataset in datasets:
            print(f"Dataset: {dataset.id}")
    else:
        # If no to_id and no prefix, try to extract a prefix
        if args.to_id is None and args.prefix is None:
            # Try to extract org
            org, repo_name = args.from_id.split('/')
            # Check if there's a common prefix pattern we can extract
            for common_prefix in ["fig1_all_", "figure1_", "test_", "eval_"]:
                if repo_name.startswith(common_prefix):
                    args.prefix = common_prefix
                    print(f"Auto-detected prefix: {args.prefix}")
                    break
            
            if args.prefix is None:
                print("Error: Either --to or --prefix must be specified")
                exit(1)
                
        # Move the repository
        move_single_repo(
            from_id=args.from_id, 
            to_id=args.to_id, 
            prefix=args.prefix,
            replace_prefix=args.replace_prefix,
            repo_type=args.type, 
            dry_run=args.dry_run
        )