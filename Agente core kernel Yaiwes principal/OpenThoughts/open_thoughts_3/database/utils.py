import logging
from typing import Any, Dict, Generator, Optional, Tuple

from datasets import DatasetDict, load_dataset
from huggingface_hub import HfApi, whoami
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.config import DATABASE_URL
from database.models import Base, Dataset, Model

logger = logging.getLogger(__name__)
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import UUID
import re
import os

HF_HUB_CACHE = os.environ.get("HF_HUB_CACHE")
if not HF_HUB_CACHE:
    print(
        "WARNING: HF_HUB_CACHE environment variable is not set, using default cache directory ~/.cache/huggingface/hub database utils"
    )

def create_db_engine():
    """
    Create and configure SQLAlchemy engine and session maker.

    Returns:
        Tuple containing:
            - SQLAlchemy Engine instance
            - Session maker factory
    """
    engine = create_engine(DATABASE_URL)
    create_tables(engine)
    return engine, sessionmaker(bind=engine)


def create_tables(engine) -> None:
    """
    Create all database tables defined in Base metadata.

    Args:
        engine: SQLAlchemy Engine instance
    """
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of database operations.

    This context manager ensures proper handling of database sessions,
    including automatic rollback on errors and proper session closure.

    Yields:
        SQLAlchemy session object for database operations

    Raises:
        Exception: Any exceptions that occur during database operations
    """
    engine, SessionMaker = create_db_engine()
    session = SessionMaker()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def check_dataset_exists(name: str, subset: str = None) -> bool:
    """
    Check if dataset exists based on name.
    Returns True or False.
    """
    if subset is not None:
        dataset = load_dataset(name, subset, cache_dir=HF_HUB_CACHE)
    else:
        dataset = load_dataset(name, cache_dir=HF_HUB_CACHE)
    if isinstance(dataset, DatasetDict):
        fingerprint = dataset["train"]._fingerprint
    else:
        fingerprint = dataset._fingerprint

    with session_scope() as session:
        dataset = session.query(Dataset).filter_by(hf_fingerprint=fingerprint).first()
        if dataset is not None:
            return True
        else:
            return False


def get_or_add_dataset_by_name(
    name: str, subset: str = None, dataset_type: str = "SFT", cache_dir: str = None
) -> Dict[str, Any]:
    """
    Retrieve or create a dataset entry by name from HuggingFace.

    Args:
        name: Name of the dataset on HuggingFace
        subset: Subset of the HF dataset. Defaults to None

    Returns:
        Dict containing dataset metadata including ID, name, creation info, etc.

    Raises:
        RuntimeError: If dataset cannot be loaded or database operations fail
    """
    if cache_dir is None:
        cache_dir = HF_HUB_CACHE
    if subset is not None:
        dataset = load_dataset(name, subset, cache_dir=cache_dir)
    else:
        dataset = load_dataset(name, cache_dir=cache_dir)
    if isinstance(dataset, DatasetDict):
        fingerprint = dataset["train"]._fingerprint
        row_count = len(dataset["train"])
    else:
        fingerprint = dataset._fingerprint
        row_count = len(dataset)

    with session_scope() as session:
        dataset = session.query(Dataset).filter_by(hf_fingerprint=fingerprint).first()
        if dataset is not None:
            return get_dataset_from_db(dataset.id, subset)

        id = uuid.uuid4()
        creation_time = datetime.now(timezone.utc)
        if os.path.exists(f"{name}"):
            # this is a local dataset path in the hf cache
            # hf_commit_hash = name.split("/")[-1] # one way of getting the commit hash
            """
            1. ^ - Anchors the match to the beginning of the string
            2. .+ - Matches one or more of any character (getting to the part with "datasets--")
            3. datasets-- - Matches the literal text "datasets--"
            4. ([^/]+) - First capture group:
                - [^/] - Any character that is NOT a forward slash
                - + - One or more of those characters
                - Captures "bespokelabs" in your example
            5. -- - Matches the literal text "--"
            6. ([^/]+) - Second capture group, captures "Bespoke-Stratos-17k"
            7. (?:/.*)? - A non-capturing group that is optional (note the ? at the end):
                - / - Matches a literal forward slash
                - .* - Matches any characters (including none)
                - This part handles any path after the dataset name
            8. $ - Anchors the match to the end of the string
            The substitution r"\1/\2" replaces the entire matched string with just the contents of the two capture groups
            separated by a slash.
            """
            # Better to recover the name so it shows up nicely in the DB
            name = re.sub(r"^.+datasets--([^/]+)--([^/]+)(?:/.*)?$", r"\1/\2", name)
        hf_commit_hash = HfApi().dataset_info(name).sha
        last_modified = HfApi().dataset_info(name).last_modified

        return upload_dataset_to_db(
            id=id,
            name=name,
            data_location="HF",
            dataset_type=dataset_type,
            generation_parameters={"meta": "auto_added_by_hf"},
            created_by=whoami()["name"],
            creation_location="HF",
            creation_time=creation_time,
            generation_start=creation_time,
            generation_end=creation_time,
            generation_status="n/a",
            is_final=True,
            is_external=True,
            hf_link=f"https://huggingface.co/datasets/{name}",
            run_id="n/a",
            git_commit_hash="n/a",
            git_diff="n/a",
            data_generation_hash="n/a",
            hf_fingerprint=fingerprint,
            hf_commit_hash=hf_commit_hash,
            row_count=row_count,
            last_modified=last_modified,
        )


def get_dataset_from_db(id: UUID, subset: str = None) -> Dict[str, Any]:
    """
    Retrieve dataset metadata from database by ID.

    Args:
        id: UUID of the dataset
        subset: Subset of the HF dataset. Defaults to None

    Returns:
        Dict containing dataset metadata

    Raises:
        RuntimeError: If dataset not found or has changed from external source
    """
    with session_scope() as session:
        dataset_db_obj = session.get(Dataset, id)
        if dataset_db_obj is None:
            raise RuntimeError(f"Dataset with id {id} not found in database")

        hf_name = dataset_db_obj.hf_link.replace(
            "https://huggingface.co/datasets/", ""
        ).rstrip("/")
        if subset is not None:
            dataset = load_dataset(hf_name, subset, cache_dir=HF_HUB_CACHE)["train"]
        else:
            dataset = load_dataset(hf_name, cache_dir=HF_HUB_CACHE)["train"]

        if isinstance(dataset, DatasetDict):
            fingerprint = dataset["train"]._fingerprint
            row_count = len(dataset["train"])
        else:
            fingerprint = dataset._fingerprint
            row_count = len(dataset)

        if fingerprint == dataset_db_obj.hf_fingerprint:
            return dataset_db_obj.to_dict()
        else:
            id = uuid.uuid4()
            logger.info(
                f"The dataset at the external link has changed, reregistering at ID: {id}"
            )

            creation_time = datetime.now(timezone.utc)
            hf_commit_hash = HfApi().dataset_info(hf_name).sha
            last_modified = HfApi().dataset_info(hf_name).last_modified

            return upload_dataset_to_db(
                id=id,
                name=dataset_db_obj.name,
                data_location=dataset_db_obj.data_location,
                dataset_type=dataset_db_obj.dataset_type,
                generation_parameters=dataset_db_obj.generation_parameters,
                created_by=dataset_db_obj.created_by,
                creation_location=dataset_db_obj.creation_location,
                creation_time=creation_time,
                generation_start=creation_time,
                generation_end=creation_time,
                generation_status=dataset_db_obj.generation_status,
                is_external=dataset_db_obj.is_external,
                is_final=dataset_db_obj.is_final,
                hf_link=dataset_db_obj.hf_link,
                run_id=dataset_db_obj.run_id,
                git_commit_hash=dataset_db_obj.git_commit_hash,
                git_diff=dataset_db_obj.git_diff,
                data_generation_hash=dataset_db_obj.data_generation_hash,
                hf_fingerprint=fingerprint,
                hf_commit_hash=hf_commit_hash,
                row_count=row_count,
                last_modified=last_modified,
            )


def upload_dataset_to_db(
    name: str,
    data_location: str,
    dataset_type: str,
    generation_parameters: Dict[str, Any],
    created_by: str,
    creation_location: str,
    generation_status: str,
    is_final: bool,
    is_external: bool,
    hf_link: str,
    run_id: str,
    git_commit_hash: str,
    git_diff: str,
    data_generation_hash: str,
    hf_fingerprint: str,
    hf_commit_hash: str,
    row_count: int,
    last_modified: datetime,
    creation_time: Optional[datetime] = None,
    generation_start: Optional[datetime] = None,
    generation_end: Optional[datetime] = None,
    id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Upload a new dataset to the database with all required fields.

    Args:
        name: Non-unique pretty name, defaults to YAML name field
        data_location: S3/GCS directory or HuggingFace link
        dataset_type: Type of dataset (SFT/RLHF)
        generation_parameters: Dictionary of generation configuration parameters
        created_by: Creator ($USER, $SLURM_USER)
        creation_location: Environment (bespoke_ray, local, TACC, etc)
        creation_time: Time this row was initially created, defaults to current time
        generation_start: Time start of generation
        generation_end: Time end of generation
        generation_status: Current status of dataset generation
        is_final: False for intermediate datasets
        is_external: True for datasets not from DCFT pipeline
        hf_link: Optional HuggingFace URL
        run_id: Shared ID of set of rows from a single dataset creation run
        git_commit_hash: Commit hash used in generation
        git_diff: Git diff of changes from commit
        data_generation_hash: Operator hash in the data generation framework
        hf_fingerprint: Fingerprint of dataset in HF repo
        hf_commit_hash: Commit hash in HF
        row_count: Number of rows in dataset
        last_modified: Last time this entry was modified
        id: Optional UUID for the dataset, generated if not provided

    Returns:
        Dict containing the metadata of the created dataset entry

    Raises:
        RuntimeError: If database operations fail
    """
    if id is None:
        id = uuid.uuid4()

    if creation_time is None:
        creation_time = datetime.now(timezone.utc)

    with session_scope() as session:
        dataset_db_obj = Dataset(
            id=id,
            name=name,
            data_location=data_location,
            dataset_type=dataset_type,
            generation_parameters=generation_parameters,
            created_by=created_by,
            creation_location=creation_location,
            creation_time=creation_time,
            generation_start=generation_start,
            generation_end=generation_end,
            generation_status=generation_status,
            is_final=is_final,
            is_external=is_external,
            hf_link=hf_link,
            run_id=run_id,
            git_commit_hash=git_commit_hash,
            git_diff=git_diff,
            data_generation_hash=data_generation_hash,
            hf_fingerprint=hf_fingerprint,
            hf_commit_hash=hf_commit_hash,
            row_count=row_count,
            last_modified=last_modified,
        )

        session.add(dataset_db_obj)
        session.commit()

        return dataset_db_obj.to_dict()


def get_model_from_db(id: "UUID") -> Model:
    """
    Given uuid, return a dict for the model entry in DB
    """
    with session_scope() as session:
        model_db_obj = session.get(Model, uuid.UUID(str(id)))
        if model_db_obj is None:
            raise RuntimeError(f"Model with id {id} not found in database")
        return model_db_obj.to_dict()


def get_or_add_model_by_name(hf_model: str):
    """
    Given hf_model path, return UUID of hf_model.
    Checks for existence by using git commit hash.
    If doesn't exist in DB, create an entry and return UUID of entry.
    If there exists more than one entry in DB, return UUID of latest model by last_modified.

    Args:
        hf_model (str): The path or identifier for the Hugging Face model.
    """
    git_commit_hash = HfApi().model_info(hf_model).sha
    with session_scope() as session:
        model_instances = (
            session.query(Model)
            .filter(Model.weights_location == hf_model)
            .filter(Model.git_commit_hash == git_commit_hash)
            .all()
        )
        model_instances = [i.to_dict() for i in model_instances]

    if len(model_instances) == 0:
        print(f"{hf_model} doesn't exist in database. Creating entry:")
        return register_hf_model_to_db(hf_model)
    elif len(model_instances) > 1:
        print(
            f"WARNING: Model {hf_model} has multiple entries in DB. Returning latest match."
        )
        model_instances = sorted(
            model_instances,
            key=lambda x: (x["last_modified"] is not None, x["last_modified"]),
        )
        for i in model_instances:
            print(f"id: {i['id']}, git_commit_hash: {i['git_commit_hash']}")
        return model_instances[-1]["id"]
    else:
        return model_instances[0]["id"]


def delete_models_by_name(name: str, contains: bool = False):
    """
    Given name, delete all models with the name.
    """
    print(contains)
    with session_scope() as session:
        if contains:
            model_instances = (
                session.query(Model).filter(Model.name.contains(name)).all()
            )
        else:
            model_instances = session.query(Model).filter(Model.name == name).all()
        model_instances = [i.to_dict() for i in model_instances]
        for i in model_instances:
            print(i["id"])
            try:
                session.query(Model).filter(Model.id == uuid.UUID(i["id"])).delete()
            except:
                print(f"Error deleting model {i['id']}")
        session.commit()
    return model_instances


def delete_model_by_uid(uid: str):
    """
    Given uid, delete the model entry from DB
    """
    with session_scope() as session:
        model_db_obj = session.get(Model, uuid.UUID(uid))
        if model_db_obj is None:
            raise RuntimeError(f"Model with id {uid} not found in database")
        session.query(Model).filter(Model.id == uuid.UUID(uid)).delete()
        session.commit()
        return model_db_obj.to_dict()


def register_hf_model_to_db(hf_model: str, force: bool = False):
    """
    Registers a new model to the database given the HF path.
    Just need the model path. Other fields are filled in automatically.
    Fails if the model already exists. Use --force if you really want to create a new entry.

    Args:
        hf_model (str): The path or identifier for the Hugging Face model.
        force (bool): If True, forces the registration of the model even if it already exists in the database.
                      If False, avoids duplicating entries for the same model. Default is False.

    Raises:
        ValueError: If the model cannot be registered due to missing metadata or if a duplicate entry
                    exists when `force` is set to False.
    """
    model_info = HfApi().model_info(hf_model)
    git_commit_hash = model_info.sha
    last_modified = model_info.lastModified

    with session_scope() as session:
        model_instances = (
            session.query(Model)
            .filter(Model.weights_location == hf_model)
            .filter(Model.git_commit_hash == git_commit_hash)
            .all()
        )
        model_instances = [i.to_dict() for i in model_instances]

    # Raise warning if model already exists
    if len(model_instances) > 0:
        if not force:
            error_msg = f"{hf_model} found {len(model_instances)} entries in db."
            for i in model_instances:
                error_msg += f"\nid: {i['id']} git_commit_hash: {git_commit_hash}"
            error_msg += "\nUse --force if you would like to create a new entry"
            raise ValueError(error_msg)

    id = uuid.uuid4()
    creation_time = datetime.now(timezone.utc)

    # Create new model entry
    with session_scope() as session:
        model = Model(
            id=id,
            name=hf_model,
            base_model_id=id,
            created_by="hf-base-model",
            creation_location="hf-base-model",
            creation_time=creation_time,
            training_start=creation_time,
            training_end=creation_time,
            training_parameters=None,
            training_status=None,
            dataset_id=None,
            is_external=True,
            weights_location=hf_model,
            wandb_link=None,
            git_commit_hash=git_commit_hash,
            last_modified=last_modified,
        )

        # Add and commit to database
        session.add(model)
        session.commit()
        print(f"Model successfully registered to db! {model}")

    return id
