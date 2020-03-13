import os
import logging
import shlex
from urllib.parse import urlparse


is_true = lambda key: os.environ.get(key, "").lower() in ["1", "true"]

BASE_PATH = os.environ.get(
    "BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_PATH", "/vendors/buildkite/secrets"
)
DEFAULT_SLUG = os.environ.get(
    "BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_DEFAULT_KEY", "global"
)
# Return an list of the secret types that we can retrieve.
# This is derived from env var BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_TYPES.
# which is a colon delimited list.
SECRET_TYPES = os.environ.get(
    "BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_TYPES", "env:ssh:git-creds"
).split(":")
MODE = os.environ.get("BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_MODE", "pipeline")


def setup_logging():
    """Logging setup"""
    logging_kwargs = {
        "filename": "/tmp/bk-ssm-secrets.log",
        "format": "[%(asctime)s][%(levelname)s] %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    if is_true("BUILDKITE_PLUGIN_AWS_PARAMSTORE_SECRETS_VERBOSE"):
        logging.basicConfig(level=logging.DEBUG, **logging_kwargs)
    else:
        logging.basicConfig(level=logging.INFO, **logging_kwargs)

def extract_ssh_agent_envars(agent_output):
    '''
    Parse the output from ssh-agent to get only the variables and values

    Sample output:
    SSH_AUTH_SOCK=/tmp/ssh-KgoPdeGP2LPZ/agent.24789; export SSH_AUTH_SOCK;
    SSH_AGENT_PID=24790; export SSH_AGENT_PID;
    echo Agent pid 24790;
    '''
    agent_env_vars = {}
    logging.debug(f"agent_output: {agent_output}")
    output = agent_output.replace('\n', '').split(';')

    for line in output:
        key_val_pair = line.split('=')
        if len(key_val_pair) == 2:
            agent_env_vars[key_val_pair[0]] = key_val_pair[1]
            os.environ[key_val_pair[0]]  = key_val_pair[1]

    return agent_env_vars


def dump_env_secrets(env_before):
    # Get difference in sets
    for key in set(os.environ) - set(env_before):
        print(f"export {key}={shlex.quote(os.environ[key])}")


def url_to_slug(url):
    parsed = urlparse(url)
    if parsed.scheme == "":
        raise ValueError(f"Invalid URL scheme found: {url}")

    slug = f"{parsed.hostname}"
    if parsed.port:
        slug += f":{parsed.port}"
    if parsed.path:
        slug += "_" + parsed.path.strip("/").replace("/", "_").replace("~", "_")
    return slug
